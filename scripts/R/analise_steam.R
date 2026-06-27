# Análise de Dados dos Jogos da Steam
# Script de análise em R

library(tidyverse)
library(ggplot2)
library(corrplot)
library(stats)

# ==================== CARREGAMENTO DOS DADOS ====================

# Definir diretório de trabalho
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Carregar dados processados
df <- read.csv("../../data/processed/steam_games_processed.csv", stringsAsFactors = FALSE)

# Visualizar estrutura dos dados
cat("Estrutura dos dados:\n")
str(df)

cat("\nPrimeiras linhas:\n")
head(df)

cat("\nResumo dos dados:\n")
summary(df)

# ==================== PRÉ-PROCESSAMENTO ====================

# Converter colunas categóricas para fatores
df$steam_deck_status <- factor(df$steam_deck_status, levels = c("Unknown", "Playable", "Verified"))
df$is_backlog <- as.logical(df$is_backlog)

# Substituir valores NA em metacritic_score se necessário
df$metacritic_score[is.na(df$metacritic_score)] <- NA

# Remover linhas com dados críticos ausentes
df_clean <- df %>%
  filter(!is.na(playtime_hours))

cat("\nDados após limpeza:", nrow(df_clean), "jogos\n")

# ==================== 1. CORRELAÇÃO METACRITIC vs TEMPO DE JOGO ====================

cat("\n\n===== ANÁLISE 1: Correlação Metacritic vs Tempo de Jogo =====\n")

# Filtrar apenas jogos com score Metacritic disponível
df_with_metacritic <- df_clean %>%
  filter(!is.na(metacritic_score))

cat("Jogos com score Metacritic:", nrow(df_with_metacritic), "\n")

if(nrow(df_with_metacritic) > 2) {
  # Calcular correlação de Pearson
  correlation <- cor(df_with_metacritic$playtime_hours, 
                     df_with_metacritic$metacritic_score, 
                     use = "complete.obs")
  
  # Teste de correlação
  cor_test <- cor.test(df_with_metacritic$playtime_hours, 
                       df_with_metacritic$metacritic_score)
  
  cat("Correlação de Pearson:", round(correlation, 4), "\n")
  cat("P-value:", round(cor_test$p.value, 4), "\n")
  cat("Interpretação: ")
  if(cor_test$p.value < 0.05) {
    cat("Correlação SIGNIFICATIVA\n")
  } else {
    cat("Correlação NÃO significativa\n")
  }
  
  # Criar visualização
  plot1 <- ggplot(df_with_metacritic, aes(x = metacritic_score, y = playtime_hours)) +
    geom_point(alpha = 0.6, color = "steelblue") +
    geom_smooth(method = "lm", se = TRUE, color = "red") +
    labs(title = "Correlação: Score Metacritic vs Tempo de Jogo",
         x = "Score Metacritic",
         y = "Tempo de Jogo (horas)",
         subtitle = paste("Correlação de Pearson =", round(correlation, 4))) +
    theme_minimal() +
    theme(plot.title = element_text(face = "bold", size = 14))
  
  ggsave("../../outputs/01_metacritic_vs_playtime.png", plot1, width = 10, height = 6)
  print(plot1)
}

# ==================== 2. ANÁLISE DO BACKLOG ====================

cat("\n\n===== ANÁLISE 2: Análise do Backlog =====\n")

backlog_summary <- df_clean %>%
  group_by(is_backlog) %>%
  summarise(
    count = n(),
    percentage = n() / nrow(df_clean) * 100,
    avg_playtime = mean(playtime_hours, na.rm = TRUE),
    .groups = 'drop'
  ) %>%
  mutate(is_backlog = ifelse(is_backlog, "Backlog", "Jogado"))

cat("Resumo do Backlog:\n")
print(as.data.frame(backlog_summary))

# Correlação between backlog e Metacritic
if(nrow(df_with_metacritic) > 0) {
  backlog_metacritic <- df_with_metacritic %>%
    group_by(is_backlog) %>%
    summarise(
      avg_metacritic = mean(metacritic_score, na.rm = TRUE),
      count = n(),
      .groups = 'drop'
    ) %>%
    mutate(is_backlog = ifelse(is_backlog, "Backlog", "Jogado"))
  
  cat("\nScore Metacritic médio por status:\n")
  print(as.data.frame(backlog_metacritic))
  
  # Visualização
  plot2 <- ggplot(backlog_metacritic, aes(x = is_backlog, y = avg_metacritic, fill = is_backlog)) +
    geom_col(alpha = 0.7) +
    geom_text(aes(label = round(avg_metacritic, 1)), vjust = -0.5, size = 4) +
    labs(title = "Score Metacritic Médio: Backlog vs Jogados",
         x = "Status",
         y = "Score Metacritic Médio",
         fill = "Status") +
    theme_minimal() +
    theme(plot.title = element_text(face = "bold", size = 14),
          legend.position = "none")
  
  ggsave("../../outputs/02_backlog_metacritic.png", plot2, width = 8, height = 6)
  print(plot2)
}

# ==================== 3. ANÁLISE STEAM DECK ====================

cat("\n\n===== ANÁLISE 3: Steam Deck Verification e Tempo de Jogo =====\n")

steam_deck_analysis <- df_clean %>%
  group_by(steam_deck_status) %>%
  summarise(
    count = n(),
    avg_playtime = mean(playtime_hours, na.rm = TRUE),
    median_playtime = median(playtime_hours, na.rm = TRUE),
    max_playtime = max(playtime_hours, na.rm = TRUE),
    .groups = 'drop'
  )

cat("Análise por status Steam Deck:\n")
print(as.data.frame(steam_deck_analysis))

# Teste ANOVA para verificar diferenças significativas
if(length(unique(df_clean$steam_deck_status)) > 1) {
  anova_test <- aov(playtime_hours ~ steam_deck_status, data = df_clean)
  cat("\nTeste ANOVA para diferenças de tempo de jogo por Steam Deck:\n")
  cat("P-value:", round(summary(anova_test)[[1]]["steam_deck_status", "Pr(>F)"], 4), "\n")
}

# Visualização
plot3 <- ggplot(df_clean, aes(x = steam_deck_status, y = playtime_hours, fill = steam_deck_status)) +
  geom_boxplot(alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.3, color = "black", size = 2) +
  labs(title = "Distribuição de Tempo de Jogo por Status Steam Deck",
       x = "Status",
       y = "Tempo de Jogo (horas)",
       fill = "Status") +
  theme_minimal() +
  theme(plot.title = element_text(face = "bold", size = 14),
        legend.position = "bottom")

ggsave("../../outputs/03_steam_deck_playtime.png", plot3, width = 10, height = 6)
print(plot3)

# ==================== 4. CATEGORIAS MAIS JOGADAS ====================

cat("\n\n===== ANÁLISE 4: Categorias Mais Jogadas =====\n")

# Separar categorias (estão em formato "categoria1; categoria2; ...")
categories_data <- df_clean %>%
  separate_rows(categories, sep = "; ") %>%
  filter(categories != "Unknown") %>%
  group_by(categories) %>%
  summarise(
    count = n(),
    total_playtime = sum(playtime_hours, na.rm = TRUE),
    avg_playtime = mean(playtime_hours, na.rm = TRUE),
    .groups = 'drop'
  ) %>%
  arrange(desc(total_playtime)) %>%
  head(15)

cat("Top 15 Categorias por Tempo Total de Jogo:\n")
print(as.data.frame(categories_data))

# Visualização - Top 10 categorias
plot4 <- ggplot(categories_data %>% head(10), aes(x = reorder(categories, total_playtime), y = total_playtime, fill = categories)) +
  geom_col(alpha = 0.7) +
  coord_flip() +
  labs(title = "Top 10 Categorias por Tempo Total de Jogo",
       x = "Categoria",
       y = "Tempo Total de Jogo (horas)",
       fill = "Categoria") +
  theme_minimal() +
  theme(plot.title = element_text(face = "bold", size = 14),
        legend.position = "none")

ggsave("../../outputs/04_top_categories.png", plot4, width = 10, height = 7)
print(plot4)

# ==================== RESUMO GERAL ====================

cat("\n\n===== RESUMO GERAL =====\n")
cat("Total de jogos:", nrow(df_clean), "\n")
cat("Total de horas jogadas:", round(sum(df_clean$playtime_hours, na.rm = TRUE), 2), "horas\n")
cat("Tempo médio por jogo:", round(mean(df_clean$playtime_hours, na.rm = TRUE), 2), "horas\n")
cat("Tempo mediano por jogo:", round(median(df_clean$playtime_hours, na.rm = TRUE), 2), "horas\n")
cat("Jogos no backlog:", backlog_summary$count[backlog_summary$is_backlog == "Backlog"], 
    sprintf("(%.1f%%)", backlog_summary$percentage[backlog_summary$is_backlog == "Backlog"]), "\n")
cat("Jogos com score Metacritic:", nrow(df_with_metacritic), "\n")

# Visualização geral
summary_stats <- data.frame(
  Métrica = c("Total de Jogos", "Horas Jogadas", "No Backlog", "Com Score Metacritic", "Verified Steam Deck"),
  Valor = c(
    nrow(df_clean),
    round(sum(df_clean$playtime_hours, na.rm = TRUE), 0),
    backlog_summary$count[backlog_summary$is_backlog == "Backlog"],
    nrow(df_with_metacritic),
    nrow(df_clean %>% filter(steam_deck_status == "Verified"))
  )
)

plot5 <- ggplot(summary_stats, aes(x = reorder(Métrica, Valor), y = Valor, fill = Métrica)) +
  geom_col(alpha = 0.7) +
  geom_text(aes(label = Valor), hjust = -0.1, size = 4) +
  coord_flip() +
  labs(title = "Resumo Geral da Análise",
       x = "",
       y = "Quantidade",
       fill = "Métrica") +
  theme_minimal() +
  theme(plot.title = element_text(face = "bold", size = 14),
        legend.position = "none")

ggsave("../../outputs/05_summary.png", plot5, width = 10, height = 6)
print(plot5)

cat("\n\nAnálise concluída! Gráficos salvos em ../../outputs/\n")

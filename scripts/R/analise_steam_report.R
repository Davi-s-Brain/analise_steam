# Relatório de Análise - Steam Games (versão simplificada)
# Usa apenas ggplot2 + base R (sem tidyverse)

library(ggplot2)

# ==================== CARREGAMENTO ====================
df <- read.csv("/home/dsouza/Documentos/Projetinhos/analise_steam/data/processed/steam_games_processed.csv", stringsAsFactors = FALSE)

# Corrigir tipos
df$playtime_hours <- as.numeric(df$playtime_hours)
df$is_backlog <- df$is_backlog == "True"

cat("========================================\n")
cat("  RELATÓRIO DE ANÁLISE STEAM GAMES\n")
cat("========================================\n\n")

# ==================== ESTATÍSTICAS GERAIS ====================
cat("===== ESTATÍSTICAS GERAIS =====\n")
cat("Total de jogos na biblioteca:", nrow(df), "\n")
cat("Total de horas jogadas:", round(sum(df$playtime_hours, na.rm=TRUE), 1), "horas\n")
cat("Tempo médio por jogo:", round(mean(df$playtime_hours, na.rm=TRUE), 1), "horas\n")
cat("Tempo mediano por jogo:", round(median(df$playtime_hours, na.rm=TRUE), 1), "horas\n")
cat("Jogos no backlog (0h):", sum(df$is_backlog), sprintf("(%.1f%%)", sum(df$is_backlog)/nrow(df)*100), "\n")
cat("Jogos jogados (>0h):", sum(!df$is_backlog), "\n\n")

# Metacritic
mc_valid <- df[!is.na(df$metacritic_score) & df$metacritic_score != "None",]
cat("Jogos com score Metacritic:", nrow(mc_valid), "\n\n")

# Steam Deck
cat("Status Steam Deck:\n")
deck_table <- table(df$steam_deck_status)
for(name in names(deck_table)) {
  cat(sprintf("  %s: %d jogos\n", name, deck_table[name]))
}
cat("\n")

# ==================== TOP 15 JOGOS POR TEMPO ====================
cat("===== TOP 15 JOGOS MAIS JOGADOS =====\n")
df_sorted <- df[order(-df$playtime_hours),]
top15 <- head(df_sorted[, c("name", "playtime_hours", "steam_deck_status", "metacritic_score")], 15)
for(i in 1:nrow(top15)) {
  mc <- ifelse(is.na(top15$metacritic_score[i]) | top15$metacritic_score[i]=="None", "s/ score", paste0("MC:", top15$metacritic_score[i]))
  cat(sprintf("%2d. %-50s %7.1fh  [%s]  %s\n", 
      i, top15$name[i], top15$playtime_hours[i], top15$steam_deck_status[i], mc))
}
cat("\n")

# ==================== TOP 15 BACKLOG (jogos NÃO jogados) ====================
cat("===== TOP 15 JOGOS NO BACKLOG (maiores) =====\n")
backlog <- df[df$is_backlog,]
backlog_sorted <- backlog[order(-backlog$playtime_hours),]
# Backlog = 0h, então vamos listar os que estão no backlog sem ordenar por tempo
backlog_names <- df[df$is_backlog, "name"]
cat(sprintf("Total de jogos no backlog: %d\n\n", length(backlog_names)))
for(i in 1:min(15, length(backlog_names))) {
  cat(sprintf("%2d. %s\n", i, backlog_names[i]))
}
cat("\n")

# ==================== ANÁLISE POR CATEGORIAS ====================
cat("===== CATEGORIAS MAIS FREQUENTES =====\n")
all_cats <- unlist(strsplit(df$categories, "; "))
all_cats <- all_cats[all_cats != "Unknown" & nchar(all_cats) > 0]
cat_table <- sort(table(all_cats), decreasing=TRUE)
cat("Top 10 categorias:\n")
for(i in 1:min(10, length(cat_table))) {
  cat(sprintf("  %2d. %-35s %d jogos\n", i, names(cat_table)[i], cat_table[i]))
}
cat("\n")

# ==================== GRÁFICOS ====================
dir.create("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs", showWarnings = FALSE, recursive = TRUE)

# Gráfico 1: Top 20 jogos mais jogados
png("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs/01_top20_playtime.png", width=1200, height=800)
top20 <- head(df_sorted, 20)
ggplot(top20, aes(x=reorder(name, playtime_hours), y=playtime_hours)) +
  geom_col(fill="steelblue", alpha=0.8) +
  geom_text(aes(label=sprintf("%.0fh", playtime_hours)), hjust=-0.1, size=3) +
  coord_flip() +
  labs(title="Top 20 Jogos Mais Jogados", x="", y="Horas Jogadas") +
  theme_minimal() +
  theme(plot.title=element_text(face="bold", size=14))
dev.off()

# Gráfico 2: Distribuição de horas jogadas
png("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs/02_playtime_distribution.png", width=1000, height=600)
ggplot(df, aes(x=playtime_hours)) +
  geom_histogram(fill="steelblue", alpha=0.7, bins=30, color="white") +
  geom_vline(xintercept=mean(df$playtime_hours, na.rm=TRUE), color="red", linetype="dashed", linewidth=1) +
  geom_vline(xintercept=median(df$playtime_hours, na.rm=TRUE), color="green", linetype="dashed", linewidth=1) +
  labs(title="Distribuição de Tempo de Jogo", x="Horas Jogadas", y="Frequência",
       subtitle="Vermelho = média | Verde = mediana") +
  theme_minimal() +
  theme(plot.title=element_text(face="bold", size=14))
dev.off()

# Gráfico 3: Backlog vs Jogados
png("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs/03_backlog_analysis.png", width=800, height=600)
backlog_stats <- data.frame(
  Categoria = c("Jogados", "Backlog"),
  Quantidade = c(sum(!df$is_backlog), sum(df$is_backlog))
)
ggplot(backlog_stats, aes(x=Categoria, y=Quantidade, fill=Categoria)) +
  geom_col(alpha=0.7) +
  geom_text(aes(label=Quantidade), vjust=-0.5, size=5) +
  labs(title="Distribuição: Jogados vs Backlog", x="", y="Número de Jogos") +
  theme_minimal() +
  theme(plot.title=element_text(face="bold", size=14), legend.position="none") +
  scale_fill_manual(values=c("Jogados"="#2ecc71", "Backlog"="#e74c3c"))
dev.off()

# Gráfico 4: Tempo de jogo por status Steam Deck
png("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs/04_steam_deck_analysis.png", width=1000, height=600)
ggplot(df, aes(x=steam_deck_status, y=playtime_hours, fill=steam_deck_status)) +
  geom_boxplot(alpha=0.7) +
  geom_jitter(width=0.2, alpha=0.3, size=1) +
  labs(title="Tempo de Jogo por Status Steam Deck", x="Status", y="Horas Jogadas") +
  theme_minimal() +
  theme(plot.title=element_text(face="bold", size=14), legend.position="none")
dev.off()

# Gráfico 5: Resumo geral
png("/home/dsouza/Documentos/Projetinhos/analise_steam/outputs/05_summary.png", width=1000, height=600)
summary_data <- data.frame(
  Metrica = c("Total Jogos", "Horas Totais", "No Backlog", "Com Metacritic", "Steam Deck Verified"),
  Valor = c(nrow(df), round(sum(df$playtime_hours, na.rm=TRUE), 0), 
            sum(df$is_backlog), nrow(mc_valid), 
            sum(df$steam_deck_status == "Verified"))
)
ggplot(summary_data, aes(x=reorder(Metrica, Valor), y=Valor, fill=Metrica)) +
  geom_col(alpha=0.7) +
  geom_text(aes(label=Valor), hjust=-0.1, size=4) +
  coord_flip() +
  labs(title="Resumo Geral da Análise", x="", y="Quantidade") +
  theme_minimal() +
  theme(plot.title=element_text(face="bold", size=14), legend.position="none")
dev.off()

cat("===== GRÁFICOS GERADOS =====\n")
cat("1. outputs/01_top20_playtime.png\n")
cat("2. outputs/02_playtime_distribution.png\n")
cat("3. outputs/03_backlog_analysis.png\n")
cat("4. outputs/04_steam_deck_analysis.png\n")
cat("5. outputs/05_summary.png\n")
cat("\nAnálise concluída com sucesso!\n")

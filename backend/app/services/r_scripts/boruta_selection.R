args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
plot_history_path <- args[3]
plot_history_pdf_path <- args[4]
plot_decision_path <- args[5]
plot_decision_pdf_path <- args[6]
dataset_name <- args[7]
outcome <- args[8]
predictors <- unlist(jsonlite::fromJSON(args[9]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[10]))
max_runs_value <- as.integer(args[11])

options(repos = c(CRAN = Sys.getenv("MEDICODE_R_PACKAGE_REPO", unset = "https://cloud.r-project.org")))
auto_install_enabled <- tolower(Sys.getenv("MEDICODE_R_AUTO_INSTALL_ENABLED", unset = "true")) %in% c("1", "true", "yes")
ensure_package <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (!isTRUE(auto_install_enabled)) {
      stop(paste0("缺少 R 包: ", pkg), call. = FALSE)
    }
    install.packages(pkg, repos = getOption("repos")[["CRAN"]])
  }
}

ensure_package("jsonlite")
ensure_package("randomForest")
ensure_package("Boruta")
ensure_package("ggplot2")
library(jsonlite)
library(randomForest)
library(Boruta)
library(ggplot2)

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
for (column_name in names(df)) {
  if (is.character(df[[column_name]])) {
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ""] <- NA
    df[[column_name]] <- trimmed
  }
}

complete_df <- df[stats::complete.cases(df[, c(outcome, predictors), drop = FALSE]), c(outcome, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 20) {
  stop("有效样本量不足，Boruta 变量筛选至少需要 20 个完整观测。", call. = FALSE)
}

family_name <- "gaussian"
event_level <- NA_character_
reference_level <- NA_character_
outcome_column <- complete_df[[outcome]]
if (is.numeric(outcome_column)) {
  unique_values <- sort(unique(outcome_column))
  if (length(unique_values) == 2 && all(unique_values %in% c(0, 1))) {
    family_name <- "binomial"
    reference_level <- "0"
    event_level <- "1"
    complete_df[[outcome]] <- factor(outcome_column, levels = c(0, 1), labels = c(reference_level, event_level))
  } else {
    complete_df[[outcome]] <- as.numeric(outcome_column)
  }
} else {
  complete_df[[outcome]] <- factor(outcome_column)
  if (nlevels(complete_df[[outcome]]) == 2) {
    family_name <- "binomial"
    reference_level <- levels(complete_df[[outcome]])[1]
    event_level <- levels(complete_df[[outcome]])[2]
  } else {
    stop("Boruta 变量筛选当前仅支持连续结局或二分类结局。", call. = FALSE)
  }
}

for (predictor in predictors) {
  column <- complete_df[[predictor]]
  if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
    complete_df[[predictor]] <- as.factor(column)
  }
}

form <- stats::as.formula(paste0("`", outcome, "` ~ ."))
set.seed(123)
boruta_fit <- Boruta::Boruta(form, data = complete_df[, c(outcome, predictors), drop = FALSE], maxRuns = max_runs_value, doTrace = 0)
boruta_fixed <- Boruta::TentativeRoughFix(boruta_fit)
stats_df <- as.data.frame(Boruta::attStats(boruta_fixed), stringsAsFactors = FALSE)
stats_df$predictor <- rownames(stats_df)
stats_df$decision <- as.character(stats_df$decision)
stats_df$selected <- stats_df$decision == "Confirmed"
stats_df <- stats_df[, c("predictor", "decision", "meanImp", "medianImp", "minImp", "maxImp", "normHits", "selected"), drop = FALSE]
colnames(stats_df) <- c("predictor", "decision", "mean_importance", "median_importance", "min_importance", "max_importance", "normalized_hits", "selected")
stats_df <- stats_df[order(factor(stats_df$decision, levels = c("Confirmed", "Tentative", "Rejected")), -stats_df$median_importance), , drop = FALSE]

selected_predictors <- stats_df$predictor[stats_df$selected]
decision_counts <- table(factor(stats_df$decision, levels = c("Confirmed", "Tentative", "Rejected")))
history_df <- as.data.frame(boruta_fit$ImpHistory, stringsAsFactors = FALSE, check.names = FALSE)
history_df$run <- seq_len(nrow(history_df))
actual_runs <- nrow(history_df)
history_columns <- setdiff(colnames(history_df), "run")
history_long <- do.call(
  rbind,
  lapply(history_columns, function(column_name) {
    data.frame(
      run = history_df$run,
      feature = column_name,
      importance = as.numeric(history_df[[column_name]]),
      stringsAsFactors = FALSE
    )
  })
)
history_long <- history_long[!is.na(history_long$importance) & is.finite(history_long$importance), , drop = FALSE]

feature_decision_map <- setNames(stats_df$decision, stats_df$predictor)
history_long$decision <- ifelse(
  history_long$feature %in% names(feature_decision_map),
  feature_decision_map[history_long$feature],
  ifelse(grepl("^shadow", history_long$feature, ignore.case = TRUE), "Shadow", "Other")
)

ordered_features <- c(stats_df$predictor, intersect(c("shadowMax", "shadowMean", "shadowMin"), history_columns))
ordered_features <- ordered_features[ordered_features %in% unique(history_long$feature)]
history_long$feature <- factor(history_long$feature, levels = rev(ordered_features))

history_boxplot_df <- history_long[history_long$decision %in% c("Confirmed", "Tentative", "Rejected"), , drop = FALSE]

history_boxplot <- ggplot(history_boxplot_df, aes(x = feature, y = importance, fill = decision)) +
  geom_boxplot(width = 0.72, outlier.alpha = 0.28, color = "#111827", linewidth = 0.35) +
  coord_flip() +
  scale_fill_manual(
    values = c(
      Confirmed = "#86efac",
      Tentative = "#fcd34d",
      Rejected = "#fca5a5"
    )
  ) +
  labs(
    title = "Boruta Importance Distribution",
    x = "Feature",
    y = "Importance",
    fill = "Decision"
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", hjust = 0.5),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "#111827", fill = NA, linewidth = 0.8),
    axis.title = element_text(color = "#111827"),
    axis.text = element_text(color = "#1f2937"),
    legend.position = "top"
  )

ggsave(plot_history_path, plot = history_boxplot, width = 10, height = 7, dpi = 180)
ggsave(plot_history_pdf_path, plot = history_boxplot, width = 10, height = 7, device = grDevices::cairo_pdf)

history_lineplot <- ggplot(history_long, aes(x = run, y = importance, group = feature, color = decision)) +
  geom_line(
    aes(
      linewidth = ifelse(decision == "Shadow", 0.9, 0.5),
      alpha = ifelse(decision == "Shadow", 0.9, 0.75)
    )
  ) +
  scale_color_manual(
    values = c(
      Confirmed = "#22c55e",
      Tentative = "#f59e0b",
      Rejected = "#2563eb",
      Shadow = "#94a3b8",
      Other = "#64748b"
    )
  ) +
  scale_linewidth_identity() +
  scale_alpha_identity() +
  labs(
    title = "Boruta Importance Evolution",
    x = "Classifier Run",
    y = "Importance",
    color = "Decision"
  ) +
  coord_cartesian(
    ylim = {
      y_min <- min(history_long$importance, na.rm = TRUE)
      y_max <- max(history_long$importance, na.rm = TRUE)
      y_pad <- max((y_max - y_min) * 0.08, 1)
      c(y_min - y_pad, y_max + y_pad)
    }
  ) +
  scale_x_continuous(breaks = scales::pretty_breaks(n = 8)) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", hjust = 0.5),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "#111827", fill = NA, linewidth = 0.8),
    axis.title = element_text(color = "#111827"),
    axis.text = element_text(color = "#1f2937"),
    legend.position = "top"
  )

ggsave(plot_decision_path, plot = history_lineplot, width = 10, height = 7, dpi = 180)
ggsave(plot_decision_pdf_path, plot = history_lineplot, width = 10, height = 7, device = grDevices::cairo_pdf)

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  predictor_variables = predictors,
  family = family_name,
  event_level = event_level,
  reference_level = reference_level,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  max_runs = max_runs_value,
  actual_runs = actual_runs,
  selected_predictors = selected_predictors,
  confirmed_count = unname(decision_counts["Confirmed"]),
  tentative_count = unname(decision_counts["Tentative"]),
  rejected_count = unname(decision_counts["Rejected"]),
  features = stats_df,
  note = paste0("Boruta completed ", actual_runs, " classifier runs (maxRuns=", max_runs_value, ") and confirmed ", length(selected_predictors), " variables.")
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = "rows", null = "null", na = "null", pretty = TRUE), output_json)

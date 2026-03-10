args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
plot_importance_path <- args[3]
plot_importance_pdf_path <- args[4]
plot_cumulative_path <- args[5]
plot_cumulative_pdf_path <- args[6]
dataset_name <- args[7]
outcome <- args[8]
predictors <- unlist(jsonlite::fromJSON(args[9]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[10]))
trees_value <- as.integer(args[11])
top_n_value <- as.integer(args[12])

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
ensure_package("ggplot2")
library(jsonlite)
library(randomForest)
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
  stop("有效样本量不足，随机森林变量筛选至少需要 20 个完整观测。", call. = FALSE)
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
    y <- factor(outcome_column, levels = c(0, 1), labels = c(reference_level, event_level))
  } else {
    y <- as.numeric(outcome_column)
  }
} else {
  y <- factor(outcome_column)
  if (nlevels(y) == 2) {
    family_name <- "binomial"
    reference_level <- levels(y)[1]
    event_level <- levels(y)[2]
  } else {
    stop("随机森林变量筛选当前仅支持连续结局或二分类结局。", call. = FALSE)
  }
}

x <- complete_df[, predictors, drop = FALSE]
for (predictor in predictors) {
  column <- x[[predictor]]
  if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
    x[[predictor]] <- as.factor(column)
  }
}

set.seed(123)
rf_fit <- randomForest::randomForest(
  x = x,
  y = y,
  ntree = trees_value,
  importance = TRUE
)

importance_matrix <- randomForest::importance(rf_fit)
importance_df <- data.frame(
  predictor = rownames(importance_matrix),
  stringsAsFactors = FALSE,
  check.names = FALSE
)

if (family_name == "binomial") {
  primary_metric <- if ("MeanDecreaseAccuracy" %in% colnames(importance_matrix)) "MeanDecreaseAccuracy" else "MeanDecreaseGini"
  secondary_metric <- if (primary_metric == "MeanDecreaseAccuracy" && "MeanDecreaseGini" %in% colnames(importance_matrix)) "MeanDecreaseGini" else NA_character_
} else {
  primary_metric <- if ("%IncMSE" %in% colnames(importance_matrix)) "%IncMSE" else "IncNodePurity"
  secondary_metric <- if (primary_metric == "%IncMSE" && "IncNodePurity" %in% colnames(importance_matrix)) "IncNodePurity" else NA_character_
}

importance_df$importance <- as.numeric(importance_matrix[, primary_metric])
importance_df$secondary_importance <- if (!is.na(secondary_metric)) as.numeric(importance_matrix[, secondary_metric]) else NA_real_
importance_df <- importance_df[order(importance_df$importance, decreasing = TRUE), , drop = FALSE]
importance_df$rank <- seq_len(nrow(importance_df))
total_importance <- sum(pmax(importance_df$importance, 0), na.rm = TRUE)
importance_df$normalized_importance <- if (is.finite(total_importance) && total_importance > 0) pmax(importance_df$importance, 0) / total_importance else NA_real_
keep_n <- min(top_n_value, nrow(importance_df))
importance_df$selected <- importance_df$rank <= keep_n
selected_predictors <- importance_df$predictor[importance_df$selected]

top_plot_df <- head(importance_df, min(20, nrow(importance_df)))
top_plot_df$predictor <- factor(top_plot_df$predictor, levels = rev(top_plot_df$predictor))

importance_plot <- ggplot(top_plot_df, aes(x = predictor, y = importance)) +
  geom_col(width = 0.72, fill = "#34d399", color = "#0f766e", linewidth = 0.5) +
  coord_flip() +
  labs(
    title = "Random Forest Variable Importance",
    x = "Predictor",
    y = primary_metric
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", hjust = 0.5),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "#111827", fill = NA, linewidth = 0.8),
    axis.title = element_text(color = "#111827"),
    axis.text = element_text(color = "#1f2937")
  )

ggsave(plot_importance_path, plot = importance_plot, width = 9, height = 7, dpi = 180)
ggsave(plot_importance_pdf_path, plot = importance_plot, width = 9, height = 7, device = grDevices::cairo_pdf)

cumulative_values <- cumsum(ifelse(is.na(importance_df$normalized_importance), 0, importance_df$normalized_importance))
cumulative_df <- data.frame(
  rank = importance_df$rank,
  cumulative_importance = cumulative_values
)
reference_y <- if (nrow(cumulative_df) > 0) cumulative_df$cumulative_importance[min(keep_n, nrow(cumulative_df))] else NA_real_

cumulative_plot <- ggplot(cumulative_df, aes(x = rank, y = cumulative_importance)) +
  geom_line(color = "#0f766e", linewidth = 0.9) +
  geom_point(color = "#0f766e", size = 2.2) +
  geom_vline(xintercept = keep_n, linetype = "dashed", color = "#f59e0b", linewidth = 0.7) +
  geom_hline(yintercept = reference_y, linetype = "dotted", color = "#94a3b8", linewidth = 0.7) +
  scale_x_continuous(breaks = scales::pretty_breaks()) +
  labs(
    title = "Cumulative Variable Importance",
    x = "Rank",
    y = "Cumulative Normalized Importance"
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", hjust = 0.5),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "#111827", fill = NA, linewidth = 0.8),
    axis.title = element_text(color = "#111827"),
    axis.text = element_text(color = "#1f2937")
  )

ggsave(plot_cumulative_path, plot = cumulative_plot, width = 9, height = 7, dpi = 180)
ggsave(plot_cumulative_pdf_path, plot = cumulative_plot, width = 9, height = 7, device = grDevices::cairo_pdf)

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  predictor_variables = predictors,
  family = family_name,
  event_level = event_level,
  reference_level = reference_level,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  trees = trees_value,
  top_n = keep_n,
  importance_metric = primary_metric,
  secondary_metric = secondary_metric,
  selected_predictors = selected_predictors,
  importance_rows = importance_df,
  note = paste0("随机森林共拟合 ", trees_value, " 棵树，按 ", primary_metric, " 排序后保留前 ", keep_n, " 个变量。")
)

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = "rows", null = "null", na = "null", pretty = TRUE), output_json)

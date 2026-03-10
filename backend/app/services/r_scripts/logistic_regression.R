args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
plot_forest_path <- args[3]
plot_forest_pdf_path <- args[4]
dataset_name <- args[5]
outcome <- args[6]
predictors <- unlist(jsonlite::fromJSON(args[7]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[8]))
alpha_value <- as.numeric(args[9])
screening_mode <- if (length(args) >= 10) args[10] else "internal"
screening_threshold_arg <- if (length(args) >= 11) args[11] else "0.1"
test_csv <- if (length(args) >= 12) args[12] else "NA"

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
backtick <- function(x) paste0("`", gsub("`", "", x, fixed = TRUE), "`")

ensure_package("jsonlite")
ensure_package("ggplot2")
ensure_package("pROC")
ensure_package("ResourceSelection")
library(jsonlite)
library(ggplot2)
library(pROC)
library(ResourceSelection)

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
if (nrow(complete_df) < 10) {
  stop("有效样本量不足，Logistic 回归至少需要 10 行完整观测。", call. = FALSE)
}

outcome_values <- unique(complete_df[[outcome]])
outcome_values <- outcome_values[!is.na(outcome_values)]
if (length(outcome_values) != 2) {
  stop("Logistic 回归因变量必须是二分类变量。", call. = FALSE)
}

if (is.numeric(complete_df[[outcome]])) {
  if (!all(sort(unique(complete_df[[outcome]])) %in% c(0, 1))) {
    stop("数值型 Logistic 因变量仅支持 0/1 编码。", call. = FALSE)
  }
  reference_level <- "0"
  event_level <- "1"
  complete_df[[outcome]] <- factor(complete_df[[outcome]], levels = c(0, 1), labels = c(reference_level, event_level))
} else {
  complete_df[[outcome]] <- factor(complete_df[[outcome]])
  if (nlevels(complete_df[[outcome]]) != 2) {
    stop("Logistic 回归因变量必须恰好有两个水平。", call. = FALSE)
  }
  reference_level <- levels(complete_df[[outcome]])[1]
  event_level <- levels(complete_df[[outcome]])[2]
}

valid_predictors <- c()
for (predictor in predictors) {
  column <- complete_df[[predictor]]
  unique_values <- unique(column[!is.na(column)])
  if (length(unique_values) >= 2) {
    if (predictor %in% categorical_predictors || is.character(column) || is.logical(column)) {
      complete_df[[predictor]] <- as.factor(column)
    }
    valid_predictors <- c(valid_predictors, predictor)
  }
}
if (length(valid_predictors) == 0) {
  stop("可用于建模的自变量不足，请检查是否存在单一取值或缺失。", call. = FALSE)
}

screening_p_threshold <- suppressWarnings(as.numeric(screening_threshold_arg))
if (is.na(screening_p_threshold)) {
  screening_p_threshold <- 0.1
}

extract_logistic_rows <- function(formula_text, data, alpha_value, drop_intercept = FALSE) {
  fit <- stats::glm(stats::as.formula(formula_text), data = data, family = stats::binomial())
  fit_summary <- summary(fit)
  coef_matrix <- fit_summary$coefficients
  conf_low <- coef_matrix[, 1] - stats::qnorm(1 - alpha_value / 2) * coef_matrix[, 2]
  conf_high <- coef_matrix[, 1] + stats::qnorm(1 - alpha_value / 2) * coef_matrix[, 2]
  coef_df <- data.frame(
    term = rownames(coef_matrix),
    coefficient = unname(coef_matrix[, 1]),
    odds_ratio = unname(exp(coef_matrix[, 1])),
    std_error = unname(coef_matrix[, 2]),
    z_value = unname(coef_matrix[, 3]),
    p_value = unname(coef_matrix[, 4]),
    conf_low = unname(exp(conf_low)),
    conf_high = unname(exp(conf_high)),
    check.names = FALSE
  )
  if (drop_intercept) {
    coef_df <- subset(coef_df, term != "(Intercept)")
  }
  coef_df
}

univariate_rows <- data.frame(
  term = character(0),
  odds_ratio = numeric(0),
  std_error = numeric(0),
  z_value = numeric(0),
  p_value = numeric(0),
  conf_low = numeric(0),
  conf_high = numeric(0),
  check.names = FALSE
)
screened_predictors <- c()
for (predictor in valid_predictors) {
  predictor_formula <- paste(backtick(outcome), "~", backtick(predictor))
  predictor_rows <- tryCatch(
    extract_logistic_rows(predictor_formula, complete_df, alpha_value, drop_intercept = TRUE),
    error = function(e) NULL
  )
  if (!is.null(predictor_rows) && nrow(predictor_rows) > 0) {
    univariate_rows <- rbind(univariate_rows, predictor_rows)
    if (screening_mode == "internal" && any(!is.na(predictor_rows$p_value) & predictor_rows$p_value < screening_p_threshold)) {
      screened_predictors <- c(screened_predictors, predictor)
    }
  }
}
if (screening_mode == "respect_input") {
  screened_predictors <- valid_predictors
} else {
  screened_predictors <- unique(screened_predictors)
  if (length(screened_predictors) == 0) {
    stop("单因素分析后没有变量满足 P < 0.1，无法进入多因素 Logistic 回归。", call. = FALSE)
  }
}

formula_text <- paste(backtick(outcome), "~", paste(vapply(screened_predictors, backtick, character(1)), collapse = " + "))
fit <- stats::glm(stats::as.formula(formula_text), data = complete_df, family = stats::binomial())
fit_summary <- summary(fit)
coef_df <- extract_logistic_rows(formula_text, complete_df, alpha_value)

compute_binary_metrics <- function(actual, probability, dataset_label) {
  actual <- as.numeric(actual)
  probability <- as.numeric(probability)
  keep <- !is.na(actual) & !is.na(probability)
  actual <- actual[keep]
  probability <- probability[keep]
  predicted <- ifelse(probability >= 0.5, 1, 0)
  tp <- sum(predicted == 1 & actual == 1)
  tn <- sum(predicted == 0 & actual == 0)
  fp <- sum(predicted == 1 & actual == 0)
  fn <- sum(predicted == 0 & actual == 1)
  precision <- if ((tp + fp) == 0) NA_real_ else tp / (tp + fp)
  recall <- if ((tp + fn) == 0) NA_real_ else tp / (tp + fn)
  auc_value <- if (length(unique(actual)) == 2) tryCatch(as.numeric(pROC::auc(actual, probability, quiet = TRUE)), error = function(e) NA_real_) else NA_real_
  hl_p_value <- tryCatch({
    group_count <- max(5L, min(10L, length(unique(probability))))
    as.numeric(ResourceSelection::hoslem.test(actual, probability, g = group_count)$p.value)
  }, error = function(e) NA_real_)
  c(
    dataset_label,
    length(actual),
    sum(actual == 1),
    auc_value,
    (tp + tn) / length(actual),
    recall,
    if ((tn + fp) == 0) NA_real_ else tn / (tn + fp),
    precision,
    if ((tn + fn) == 0) NA_real_ else tn / (tn + fn),
    if (is.na(precision) || is.na(recall) || (precision + recall) == 0) NA_real_ else 2 * precision * recall / (precision + recall),
    mean((probability - actual) ^ 2),
    hl_p_value
  )
}

train_actual <- ifelse(complete_df[[outcome]] == event_level, 1, 0)
train_probability <- as.numeric(stats::predict(fit, newdata = complete_df, type = "response"))
metrics_rows <- list(compute_binary_metrics(train_actual, train_probability, "训练集"))

if (!is.na(test_csv) && nzchar(test_csv) && file.exists(test_csv)) {
  test_df <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  for (column_name in names(test_df)) {
    if (is.character(test_df[[column_name]])) {
      trimmed <- trimws(test_df[[column_name]])
      trimmed[trimmed == ""] <- NA
      test_df[[column_name]] <- trimmed
    }
  }
  if (all(c(outcome, screened_predictors) %in% names(test_df))) {
    aligned_test <- test_df[stats::complete.cases(test_df[, c(outcome, screened_predictors), drop = FALSE]), c(outcome, screened_predictors), drop = FALSE]
    if (nrow(aligned_test) > 0) {
      if (is.numeric(aligned_test[[outcome]])) {
        aligned_test[[outcome]] <- factor(aligned_test[[outcome]], levels = c(0, 1), labels = c(reference_level, event_level))
      } else {
        aligned_test[[outcome]] <- factor(aligned_test[[outcome]], levels = levels(complete_df[[outcome]]))
      }
      for (predictor in screened_predictors) {
        if (is.factor(complete_df[[predictor]])) {
          aligned_test[[predictor]] <- factor(aligned_test[[predictor]], levels = levels(complete_df[[predictor]]))
        }
      }
      aligned_test <- aligned_test[stats::complete.cases(aligned_test), c(outcome, screened_predictors), drop = FALSE]
      if (nrow(aligned_test) > 0) {
        test_actual <- ifelse(aligned_test[[outcome]] == event_level, 1, 0)
        test_probability <- as.numeric(stats::predict(fit, newdata = aligned_test, type = "response"))
        metrics_rows[[length(metrics_rows) + 1]] <- compute_binary_metrics(test_actual, test_probability, "测试集")
      }
    }
  }
}

model_chisq <- fit$null.deviance - fit$deviance
model_df <- fit$df.null - fit$df.residual
model_p <- stats::pchisq(model_chisq, df = model_df, lower.tail = FALSE)
pseudo_r2 <- if (isTRUE(fit$null.deviance == 0)) NA_real_ else 1 - fit$deviance / fit$null.deviance

result <- list(
  dataset_name = dataset_name,
  outcome_variable = outcome,
  event_level = event_level,
  reference_level = reference_level,
  predictor_variables = screened_predictors,
  sample_size = nrow(complete_df),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  pseudo_r_squared = pseudo_r2,
  aic = stats::AIC(fit),
  null_deviance = fit$null.deviance,
  residual_deviance = fit$deviance,
  df_model = model_df,
  df_residual = fit$df.residual,
  model_p_value = model_p,
  formula = formula_text,
  assumptions = list(
    "因变量必须是二分类变量，自变量可为数值型或分类变量。",
    "模型默认使用完整案例进行拟合，含缺失值的记录已剔除。",
    "OR > 1 表示事件发生优势升高，OR < 1 表示优势降低。",
    if (screening_mode == "internal") {
      paste0("先进行单因素 Logistic 回归筛选，P < ", screening_p_threshold, " 的变量纳入多因素模型。")
    } else {
      "当前工作流已提供上游筛选变量集，多因素模型直接使用输入变量建模。"
    },
    "请进一步检查样本量、稀疏单元和多重共线性，以判断模型稳健性。"
  ),
  metrics_rows = metrics_rows,
  hosmer_lemeshow_p_value = as.numeric(metrics_rows[[1]][12]),
  univariate_coefficients = univariate_rows,
  coefficients = coef_df,
  note = paste0(
    "事件水平设为 ", event_level, "，参考水平为 ", reference_level,
    if (screening_mode == "internal") paste0("；单因素 P < ", screening_p_threshold, " 纳入多因素分析；") else "；已直接使用上游筛选变量；",
    "入模变量：",
    paste(screened_predictors, collapse = ", "), "。"
  )
)

p <- NULL
png(filename = plot_forest_path, width = 2400, height = max(980, 360 + 102 * max(nrow(coef_df) - 1, 1)), res = 300)
tryCatch({
  plot_df <- subset(coef_df, term != "(Intercept)")
  if (nrow(plot_df) == 0) {
    plot_df <- coef_df
  }

  pretty_term <- function(term) {
    label <- gsub("_", " ", as.character(term), fixed = TRUE)
    label <- gsub("([[:alpha:][:space:]]+)([0-9]+)$", "\\1 = \\2", label, perl = TRUE)
    trimws(label)
  }

  plot_df$term_label <- vapply(plot_df$term, pretty_term, character(1))
  plot_df$term_label <- factor(plot_df$term_label, levels = rev(plot_df$term_label))
  plot_df$signal <- ifelse(!is.na(plot_df$p_value) & plot_df$p_value < alpha_value, "Significant", "Not significant")

  xmin <- min(plot_df$conf_low, na.rm = TRUE)
  xmax <- max(plot_df$conf_high, na.rm = TRUE)
  candidate_breaks <- c(0.2, 0.33, 0.5, 0.67, 1, 1.5, 2, 3, 4, 6, 8)
  x_breaks <- candidate_breaks[candidate_breaks >= xmin * 0.95 & candidate_breaks <= xmax * 1.05]
  if (!1 %in% x_breaks) {
    x_breaks <- sort(unique(c(x_breaks, 1)))
  }
  if (length(x_breaks) < 4) {
    x_breaks <- sort(unique(c(signif(xmin, 2), 1, signif(xmax, 2))))
  }

  p <- ggplot(plot_df, aes(x = odds_ratio, y = term_label)) +
    geom_vline(xintercept = 1, linewidth = 0.5, linetype = "dashed", color = "#64748b") +
    geom_errorbarh(
      aes(xmin = conf_low, xmax = conf_high, color = signal),
      height = 0.16,
      linewidth = 0.95
    ) +
    geom_point(
      aes(fill = signal),
      shape = 21,
      size = 3.4,
      stroke = 0.95,
      color = "#0f172a"
    ) +
    scale_x_log10(breaks = x_breaks, labels = function(x) format(x, trim = TRUE, scientific = FALSE)) +
    scale_y_discrete(expand = expansion(add = c(0.55, 0.55))) +
    scale_color_manual(values = c("Significant" = "#0f766e", "Not significant" = "#94a3b8")) +
    scale_fill_manual(values = c("Significant" = "#22c1b4", "Not significant" = "#f8fafc")) +
    labs(
      x = "Odds ratio",
      y = NULL
    ) +
    theme_minimal(base_size = 10) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major.y = element_blank(),
      panel.grid.major.x = element_line(color = "#e2e8f0", linewidth = 0.45),
      panel.border = element_rect(color = "#0f172a", fill = NA, linewidth = 0.7),
      axis.line.x = element_line(color = "#0f172a", linewidth = 0.6),
      axis.ticks.x = element_line(color = "#0f172a", linewidth = 0.55),
      axis.ticks.length = grid::unit(2.5, "pt"),
      axis.text.y = element_text(color = "#0f172a", face = "bold", size = 10, margin = margin(r = 4)),
      axis.text.x = element_text(color = "#334155"),
      axis.title.x = element_text(color = "#334155", margin = margin(t = 10), face = "bold"),
      plot.title = element_text(color = "#0f172a", face = "bold", size = 15, margin = margin(b = 4)),
      plot.subtitle = element_text(color = "#64748b", size = 10.5, margin = margin(b = 12)),
      plot.background = element_rect(fill = "white", color = NA),
      panel.background = element_rect(fill = "white", color = NA),
      plot.margin = margin(22, 24, 22, 20),
      legend.position = "none",
      axis.title.y = element_blank()
    )
  print(p)
}, error = function(e) {
  plot.new()
  text(0.5, 0.5, "Forest plot could not be generated")
})
suppressWarnings(dev.off())

grDevices::pdf(
  file = plot_forest_pdf_path,
  width = 10.5,
  height = max(5.3, 2.35 + 0.17 * max(nrow(coef_df) - 1, 1)),
  useDingbats = FALSE
)
tryCatch({
  if (!is.null(p)) {
    print(p)
  } else {
    stop("plot not ready")
  }
}, error = function(e) {
  plot.new()
  text(0.5, 0.5, "Forest plot could not be generated")
})
suppressWarnings(dev.off())

writeLines(jsonlite::toJSON(result, auto_unbox = TRUE, dataframe = "rows", null = "null", na = "null", pretty = TRUE), output_json)

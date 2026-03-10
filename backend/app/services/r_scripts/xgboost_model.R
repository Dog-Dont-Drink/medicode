args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_json <- args[3]
plot_roc_path <- args[4]
plot_roc_pdf_path <- args[5]
plot_importance_path <- args[6]
plot_importance_pdf_path <- args[7]
dataset_name <- args[8]
outcome <- args[9]
predictors <- unlist(jsonlite::fromJSON(args[10]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[11]))
eta_value <- as.numeric(args[12])
depth_value <- as.integer(args[13])
rounds_value <- as.integer(args[14])
seed_value <- as.integer(args[15])

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
script_dir <- dirname(normalizePath(sub("^--file=", "", commandArgs(FALSE)[grep("^--file=", commandArgs(FALSE))][1])))
source(file.path(script_dir, "ml_model_common.R"))

ensure_package("jsonlite")
ensure_package("ggplot2")
ensure_package("xgboost")
library(jsonlite)
library(ggplot2)
library(xgboost)

set.seed(seed_value)

train_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
train_df <- trim_dataframe_strings(train_df)
columns <- c(outcome, predictors)
complete_train <- train_df[stats::complete.cases(train_df[, columns, drop = FALSE]), columns, drop = FALSE]
excluded_rows <- nrow(train_df) - nrow(complete_train)
if (nrow(complete_train) < 20) {
  stop("XGBoost 建模至少需要 20 行完整观测。", call. = FALSE)
}

task_kind <- "classification"
if (is.numeric(complete_train[[outcome]])) {
  numeric_outcome <- suppressWarnings(as.numeric(complete_train[[outcome]]))
  numeric_levels <- unique(numeric_outcome[!is.na(numeric_outcome)])
  if (length(numeric_levels) < 2) {
    stop("结局变量需要至少两个不同取值。", call. = FALSE)
  }
  if (length(numeric_levels) != 2) {
    task_kind <- "regression"
  }
} else {
  outcome_levels <- unique(complete_train[[outcome]])
  outcome_levels <- outcome_levels[!is.na(outcome_levels)]
  if (length(outcome_levels) != 2) {
    stop("当前仅支持二分类或连续型结局（不支持多分类结局）。", call. = FALSE)
  }
}

reference_level <- ""
event_level <- ""
train_y <- numeric(0)
if (task_kind == "classification") {
  ensure_package("pROC")
  ensure_package("ResourceSelection")
  suppressPackageStartupMessages(library(pROC))
  suppressPackageStartupMessages(library(ResourceSelection))
  outcome_info <- prepare_binary_outcome(complete_train, outcome)
  complete_train <- outcome_info$data
  train_y <- outcome_info$outcome_numeric
  reference_level <- outcome_info$reference_level
  event_level <- outcome_info$event_level
} else {
  train_y <- as.numeric(complete_train[[outcome]])
}

predictor_info <- factorize_predictors(complete_train, predictors, categorical_predictors)
complete_train <- predictor_info$data
valid_predictors <- predictor_info$valid_predictors
if (length(valid_predictors) == 0) {
  stop("XGBoost 无可用预测变量。", call. = FALSE)
}

complete_test <- NULL
test_y <- numeric(0)
if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
  raw_test <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_test <- trim_dataframe_strings(raw_test)
  available_columns <- intersect(columns, names(raw_test))
  if (length(available_columns) == length(columns)) {
    candidate_test <- raw_test[stats::complete.cases(raw_test[, columns, drop = FALSE]), columns, drop = FALSE]
    if (nrow(candidate_test) > 0) {
      if (task_kind == "classification") {
        candidate_info <- prepare_binary_outcome(candidate_test, outcome)
        complete_test <- candidate_info$data
        test_y <- candidate_info$outcome_numeric
      } else {
        complete_test <- candidate_test
        test_y <- as.numeric(candidate_test[[outcome]])
      }
    }
  }
}

design <- prepare_xgb_matrices(complete_train, complete_test, valid_predictors, categorical_predictors)
train_matrix <- xgboost::xgb.DMatrix(data = design$train_matrix, label = train_y)
test_matrix <- if (!is.null(design$test_matrix)) xgboost::xgb.DMatrix(data = design$test_matrix, label = test_y) else NULL

fit <- xgboost::xgb.train(
  params = list(
    objective = if (task_kind == "classification") "binary:logistic" else "reg:squarederror",
    eval_metric = if (task_kind == "classification") "auc" else "rmse",
    eta = eta_value,
    max_depth = depth_value,
    subsample = 0.8,
    colsample_bytree = 0.8,
    seed = seed_value
  ),
  data = train_matrix,
  nrounds = rounds_value,
  verbose = 0
)

train_prob <- NULL
test_prob <- NULL
train_pred <- NULL
test_pred <- NULL
train_metrics <- NULL
test_metrics <- NULL
train_reg_metrics <- NULL
test_reg_metrics <- NULL
if (task_kind == "classification") {
  train_prob <- as.numeric(predict(fit, train_matrix))
  test_prob <- if (!is.null(test_matrix)) as.numeric(predict(fit, test_matrix)) else NULL
  train_metrics <- compute_binary_metrics(train_y, train_prob, threshold = 0.5)
  test_metrics <- if (!is.null(test_prob)) compute_binary_metrics(test_y, test_prob, threshold = 0.5) else NULL
} else {
  train_pred <- as.numeric(predict(fit, train_matrix))
  test_pred <- if (!is.null(test_matrix)) as.numeric(predict(fit, test_matrix)) else NULL
  train_reg_metrics <- compute_regression_metrics(train_y, train_pred)
  test_reg_metrics <- if (!is.null(test_pred)) compute_regression_metrics(test_y, test_pred) else NULL
}

hosmer_p <- function(actual, probability) {
  tryCatch({
    group_count <- max(5L, min(10L, length(unique(probability))))
    as.numeric(ResourceSelection::hoslem.test(actual, probability, g = group_count)$p.value)
  }, error = function(e) NA_real_)
}
train_hl <- if (task_kind == "classification") hosmer_p(train_y, train_prob) else NA_real_
test_hl <- if (task_kind == "classification" && !is.null(test_prob)) hosmer_p(test_y, test_prob) else NA_real_

importance_df <- xgboost::xgb.importance(model = fit, feature_names = design$feature_names)
if (nrow(importance_df) == 0) {
  importance_df <- data.frame(Feature = design$feature_names, Gain = NA_real_, Cover = NA_real_, Frequency = NA_real_, stringsAsFactors = FALSE)
}
importance_df <- importance_df[order(-importance_df$Gain), , drop = FALSE]
importance_df$rank <- seq_len(nrow(importance_df))
max_gain <- max(importance_df$Gain, na.rm = TRUE)
importance_df$gain_scaled <- if (is.finite(max_gain) && max_gain > 0) importance_df$Gain / max_gain else NA_real_

metrics_rows <- NULL
regression_metrics_rows <- NULL
if (task_kind == "classification") {
  metrics_rows <- list(
    c("训练集", train_metrics$sample_size, train_metrics$event_count, train_metrics$auc, train_metrics$accuracy, train_metrics$sensitivity, train_metrics$specificity, train_metrics$precision, train_metrics$npv, train_metrics$f1, train_metrics$brier_score, train_hl)
  )
  if (!is.null(test_metrics)) {
    metrics_rows[[length(metrics_rows) + 1]] <- c("测试集", test_metrics$sample_size, test_metrics$event_count, test_metrics$auc, test_metrics$accuracy, test_metrics$sensitivity, test_metrics$specificity, test_metrics$precision, test_metrics$npv, test_metrics$f1, test_metrics$brier_score, test_hl)
  }

  curve_rows <- data.frame()
  roc_sets <- list(list(label = "Train", actual = train_y, prob = train_prob))
  if (!is.null(test_prob)) {
    roc_sets[[length(roc_sets) + 1]] <- list(label = "Test", actual = test_y, prob = test_prob)
  }
  for (item in roc_sets) {
    if (length(unique(item$actual)) < 2) {
      next
    }
    roc_obj <- pROC::roc(item$actual, item$prob, quiet = TRUE)
    curve_df <- data.frame(
      specificity = roc_obj$specificities,
      sensitivity = roc_obj$sensitivities,
      dataset = item$label,
      stringsAsFactors = FALSE
    )
    curve_df$fpr <- 1 - curve_df$specificity
    curve_rows <- rbind(curve_rows, curve_df)
  }

  roc_plot <- ggplot() + theme_bw(base_size = 11)
  png(filename = plot_roc_path, width = 2200, height = 1600, res = 300)
  tryCatch({
    if (nrow(curve_rows) > 0) {
      roc_plot <- ggplot(curve_rows, aes(x = fpr, y = sensitivity, color = dataset)) +
        geom_line(linewidth = 1.1) +
        geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "#94a3b8") +
        scale_color_manual(values = c("Train" = "#0f766e", "Test" = "#7c3aed")) +
        coord_equal(xlim = c(0, 1), ylim = c(0, 1), expand = FALSE) +
        labs(
          title = "XGBoost ROC Curve",
          x = "1 - Specificity",
          y = "Sensitivity",
          color = "Dataset"
        ) +
        theme_bw(base_size = 11) +
        theme(
          panel.grid.minor = element_blank(),
          plot.title = element_text(face = "bold", size = 12),
          legend.position = "top"
        )
    } else {
      roc_plot <- ggplot(data.frame(x = 0, y = 0), aes(x, y)) +
        geom_blank() +
        labs(title = "XGBoost ROC Curve", x = "1 - Specificity", y = "Sensitivity") +
        theme_bw(base_size = 11)
    }
    print(roc_plot)
  }, finally = {
    dev.off()
  })
  ggsave(plot_roc_pdf_path, roc_plot, width = 7.2, height = 5.4, device = cairo_pdf)
} else {
  regression_metrics_rows <- list(
    c("训练集", train_reg_metrics$sample_size, train_reg_metrics$rmse, train_reg_metrics$mae, train_reg_metrics$r_squared)
  )
  if (!is.null(test_reg_metrics)) {
    regression_metrics_rows[[length(regression_metrics_rows) + 1]] <- c("测试集", test_reg_metrics$sample_size, test_reg_metrics$rmse, test_reg_metrics$mae, test_reg_metrics$r_squared)
  }

  plot_df <- data.frame(observed = train_y, predicted = train_pred, dataset = "Train", stringsAsFactors = FALSE)
  if (!is.null(test_pred)) {
    plot_df <- rbind(plot_df, data.frame(observed = test_y, predicted = test_pred, dataset = "Test", stringsAsFactors = FALSE))
  }
  pred_plot <- ggplot(plot_df, aes(x = observed, y = predicted, color = dataset)) +
    geom_point(alpha = 0.65, size = 1.4) +
    geom_abline(intercept = 0, slope = 1, linetype = "dashed", color = "#94a3b8", linewidth = 0.9) +
    scale_color_manual(values = c("Train" = "#0f766e", "Test" = "#7c3aed")) +
    labs(
      title = "XGBoost: Predicted vs Observed",
      x = "Observed",
      y = "Predicted",
      color = "Dataset"
    ) +
    theme_bw(base_size = 11) +
    theme(
      panel.grid.minor = element_blank(),
      plot.title = element_text(face = "bold", size = 12),
      legend.position = "top"
    )

  png(filename = plot_roc_path, width = 2200, height = 1600, res = 300)
  tryCatch({
    print(pred_plot)
  }, finally = {
    dev.off()
  })
  ggsave(plot_roc_pdf_path, pred_plot, width = 7.2, height = 5.4, device = cairo_pdf)
}

top_importance <- utils::head(importance_df, 15)
top_importance$Feature <- factor(top_importance$Feature, levels = rev(top_importance$Feature))
importance_plot <- ggplot(top_importance, aes(x = Feature, y = Gain)) +
  geom_col(fill = "#8b5cf6", color = "#0f172a", linewidth = 0.35) +
  coord_flip() +
  labs(
    title = "XGBoost Feature Importance",
    x = NULL,
    y = "Gain"
  ) +
  theme_bw(base_size = 11) +
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold")
  )

png(filename = plot_importance_path, width = 2200, height = 1800, res = 300)
tryCatch({
  print(importance_plot)
}, finally = {
  dev.off()
})
ggsave(plot_importance_pdf_path, importance_plot, width = 7.4, height = 6.0, device = cairo_pdf)

result <- list(
  dataset_name = dataset_name,
  model_type = "xgboost",
  task_kind = task_kind,
  outcome_variable = outcome,
  predictor_variables = valid_predictors,
  event_level = event_level,
  reference_level = reference_level,
  sample_size = nrow(complete_train),
  excluded_rows = excluded_rows,
  eta = eta_value,
  max_depth = depth_value,
  nrounds = rounds_value,
  seed = seed_value,
  metrics_rows = metrics_rows,
  regression_metrics_rows = regression_metrics_rows,
  importance_rows = data.frame(
    predictor = importance_df$Feature,
    importance = importance_df$Gain,
    secondary_importance = importance_df$Cover,
    tertiary_importance = importance_df$Frequency,
    importance_scaled = importance_df$gain_scaled,
    rank = importance_df$rank,
    stringsAsFactors = FALSE
  ),
  note = paste0(
    "XGBoost 模型已完成：eta=", eta_value,
    ", max_depth=", depth_value,
    ", nrounds=", rounds_value,
    ", seed=", seed_value,
    if (task_kind == "classification") {
      if (!is.null(test_metrics)) "；同时输出训练集与测试集性能。" else "；当前未检测到测试集，因此仅输出训练集性能。"
    } else {
      if (!is.null(test_reg_metrics)) "；当前为回归任务，输出训练集与测试集回归指标。" else "；当前为回归任务，未检测到测试集，仅输出训练集指标。"
    }
  )
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")

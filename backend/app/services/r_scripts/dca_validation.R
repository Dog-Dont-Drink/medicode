args <- commandArgs(trailingOnly = TRUE)
train_csv <- args[1]
test_csv <- args[2]
output_json <- args[3]
train_plot_path <- args[4]
train_plot_pdf_path <- args[5]
test_plot_path <- args[6]
test_plot_pdf_path <- args[7]
dataset_name <- args[8]
model_type <- args[9]
outcome <- args[10]
predictors <- unlist(jsonlite::fromJSON(args[11]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[12]))
model_params <- jsonlite::fromJSON(args[13], simplifyVector = TRUE)
range_text <- args[14]
step_value <- as.numeric(args[15])

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
ensure_package("scales")
library(jsonlite)
library(ggplot2)

open_png_device <- function(path, width, height, res) {
  tryCatch(
    grDevices::png(filename = path, width = width, height = height, res = res, type = "cairo"),
    error = function(e) grDevices::png(filename = path, width = width, height = height, res = res)
  )
}

fit_binary_model <- function(model_type, train_df, outcome, predictors, categorical_predictors, params) {
  if (model_type == "logistic") {
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(model_type = model_type, model = stats::glm(stats::as.formula(formula_text), data = train_df, family = stats::binomial()), train_df = train_df))
  }
  if (model_type == "random-forest") {
    ensure_package("randomForest")
    suppressPackageStartupMessages(library(randomForest))
    trees_value <- if (!is.null(params$trees)) as.integer(params$trees) else 500L
    mtry_value <- parse_mtry_arg(if (!is.null(params$mtry)) params$mtry else "sqrt(p)", length(predictors))
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(model_type = model_type, model = randomForest::randomForest(stats::as.formula(formula_text), data = train_df, ntree = trees_value, mtry = mtry_value), train_df = train_df))
  }
  if (model_type == "xgboost") {
    ensure_package("xgboost")
    eta_value <- if (!is.null(params$eta)) as.numeric(params$eta) else 0.05
    depth_value <- if (!is.null(params$depth)) as.integer(params$depth) else 4L
    rounds_value <- if (!is.null(params$rounds)) as.integer(params$rounds) else 300L
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    design <- prepare_xgb_matrices(train_df, NULL, predictors, categorical_predictors)
    train_matrix <- xgboost::xgb.DMatrix(data = design$train_matrix, label = ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0))
    fit <- xgboost::xgb.train(
      params = list(objective = "binary:logistic", eval_metric = "auc", eta = eta_value, max_depth = depth_value, subsample = 0.8, colsample_bytree = 0.8, seed = seed_value),
      data = train_matrix,
      nrounds = rounds_value,
      verbose = 0
    )
    return(list(model_type = model_type, model = fit, train_df = train_df))
  }
  stop("DCA 暂不支持当前模型类型。", call. = FALSE)
}

compute_dca_rows <- function(actual, probability, thresholds) {
  actual <- as.numeric(actual)
  probability <- as.numeric(probability)
  keep <- !is.na(actual) & !is.na(probability)
  actual <- actual[keep]
  probability <- probability[keep]
  n <- length(actual)
  if (n == 0) {
    return(data.frame(
      threshold = thresholds,
      model_net_benefit = rep(NA_real_, length(thresholds)),
      treat_all_net_benefit = rep(NA_real_, length(thresholds)),
      treat_none_net_benefit = rep(0, length(thresholds)),
      stringsAsFactors = FALSE
    ))
  }
  prevalence <- mean(actual == 1)
  rows <- data.frame(
    threshold = thresholds,
    model_net_benefit = NA_real_,
    treat_all_net_benefit = NA_real_,
    treat_none_net_benefit = 0,
    stringsAsFactors = FALSE
  )
  for (i in seq_along(thresholds)) {
    pt <- thresholds[i]
    predicted_positive <- probability >= pt
    tp <- sum(predicted_positive & actual == 1)
    fp <- sum(predicted_positive & actual == 0)
    rows$model_net_benefit[i] <- (tp / n) - (fp / n) * (pt / (1 - pt))
    rows$treat_all_net_benefit[i] <- prevalence - (1 - prevalence) * (pt / (1 - pt))
  }
  rows
}

make_dca_plot <- function(dca_rows, dataset_label) {
  plot_df <- rbind(
    data.frame(threshold = dca_rows$threshold, net_benefit = dca_rows$model_net_benefit, strategy = "Model"),
    data.frame(threshold = dca_rows$threshold, net_benefit = dca_rows$treat_all_net_benefit, strategy = "Treat all"),
    data.frame(threshold = dca_rows$threshold, net_benefit = dca_rows$treat_none_net_benefit, strategy = "Treat none")
  )

  x_max <- max(dca_rows$threshold, na.rm = TRUE)
  if (!is.finite(x_max)) {
    x_max <- 1
  }
  y_min_raw <- min(plot_df$net_benefit, na.rm = TRUE)
  y_max_raw <- max(plot_df$net_benefit, na.rm = TRUE)
  y_min_raw <- if (is.finite(y_min_raw)) y_min_raw else 0
  y_max_raw <- if (is.finite(y_max_raw)) y_max_raw else 0.1
  y_min <- min(0, y_min_raw)
  y_max <- max(0, y_max_raw)
  y_range <- y_max - y_min
  y_pad <- if (y_range <= 0) 0.08 else y_range * 0.06
  y_lower <- y_min - y_pad
  y_upper <- y_max + y_pad

  ggplot(plot_df, aes(x = threshold, y = net_benefit, color = strategy)) +
    geom_hline(yintercept = 0, linewidth = 0.7, color = "#94a3b8") +
    geom_line(linewidth = 1.1) +
    scale_color_manual(values = c("Model" = "#0072B2", "Treat all" = "#D55E00", "Treat none" = "#6B7280")) +
    coord_cartesian(xlim = c(0, x_max), ylim = c(y_lower, y_upper)) +
    scale_x_continuous(
      breaks = scales::pretty_breaks(n = 6),
      labels = scales::number_format(accuracy = 0.01),
      expand = expansion(mult = c(0, 0.01))
    ) +
    scale_y_continuous(
      breaks = scales::pretty_breaks(n = 6),
      labels = scales::number_format(accuracy = 0.01),
      expand = expansion(mult = c(0, 0.02))
    ) +
    labs(
      title = "Decision Curve Analysis",
      subtitle = paste0("Dataset: ", dataset_label),
      x = "Threshold probability",
      y = "Net benefit",
      color = NULL
    ) +
    theme_bw(base_size = 12) +
    theme(
      panel.grid.minor = element_blank(),
      panel.border = element_rect(color = "#0f172a", fill = NA, linewidth = 0.8),
      axis.title = element_text(size = 11, color = "#0f172a"),
      axis.text = element_text(size = 10, color = "#0f172a"),
      plot.title = element_text(face = "bold", size = 13, color = "#0f172a"),
      legend.position = "top",
      legend.text = element_text(size = 10),
      plot.subtitle = element_text(size = 10, color = "#475569")
    )
}

predict_binary_model <- function(fit_bundle, new_df, outcome, predictors, categorical_predictors) {
  if (fit_bundle$model_type == "logistic") {
    aligned_df <- new_df
    for (predictor in predictors) {
      if (is.factor(fit_bundle$train_df[[predictor]])) {
        aligned_df[[predictor]] <- factor(aligned_df[[predictor]], levels = levels(fit_bundle$train_df[[predictor]]))
      }
    }
    return(as.numeric(stats::predict(fit_bundle$model, newdata = aligned_df, type = "response")))
  }
  if (fit_bundle$model_type == "random-forest") {
    aligned_df <- new_df
    for (predictor in predictors) {
      if (is.factor(fit_bundle$train_df[[predictor]])) {
        aligned_df[[predictor]] <- factor(aligned_df[[predictor]], levels = levels(fit_bundle$train_df[[predictor]]))
      }
    }
    return(as.numeric(stats::predict(fit_bundle$model, newdata = aligned_df, type = "prob")[, levels(fit_bundle$train_df[[outcome]])[2]]))
  }
  if (fit_bundle$model_type == "xgboost") {
    design <- prepare_xgb_matrices(fit_bundle$train_df, new_df, predictors, categorical_predictors)
    matrix <- xgboost::xgb.DMatrix(data = design$test_matrix)
    return(as.numeric(predict(fit_bundle$model, matrix)))
  }
  stop("DCA 暂不支持当前模型类型。", call. = FALSE)
}

train_df <- read.csv(train_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
train_df <- trim_dataframe_strings(train_df)
columns <- c(outcome, predictors)
train_df <- train_df[stats::complete.cases(train_df[, columns, drop = FALSE]), columns, drop = FALSE]
train_info <- prepare_binary_outcome(train_df, outcome)
train_df <- train_info$data
factor_info <- factorize_predictors(train_df, predictors, categorical_predictors)
train_df <- factor_info$data
valid_predictors <- factor_info$valid_predictors
if (length(valid_predictors) == 0) {
  stop("DCA 无可用预测变量。", call. = FALSE)
}

fit_bundle <- fit_binary_model(model_type, train_df, outcome, valid_predictors, categorical_predictors, model_params)
threshold_range <- parse_threshold_range(range_text)
step_value <- if (is.na(step_value) || step_value <= 0) 0.01 else step_value
thresholds <- seq(threshold_range[1], threshold_range[2], by = step_value)
train_probability <- predict_binary_model(fit_bundle, train_df, outcome, valid_predictors, categorical_predictors)
train_actual <- ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)
train_dca_rows <- compute_dca_rows(train_actual, train_probability, thresholds)
train_plot_obj <- make_dca_plot(train_dca_rows, "Train set")
open_png_device(train_plot_path, width = 2400, height = 1600, res = 300)
tryCatch(
  {
    print(train_plot_obj)
  },
  finally = {
    grDevices::dev.off()
  }
)
ggsave(train_plot_pdf_path, train_plot_obj, width = 7.6, height = 5.3, device = cairo_pdf)

has_test <- FALSE
test_dca_rows <- NULL
if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
  raw_test <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
  raw_test <- trim_dataframe_strings(raw_test)
  if (all(columns %in% names(raw_test))) {
    candidate_test <- raw_test[stats::complete.cases(raw_test[, columns, drop = FALSE]), columns, drop = FALSE]
    if (nrow(candidate_test) > 0) {
      test_info <- prepare_binary_outcome(candidate_test, outcome)
      test_df <- test_info$data
      test_probability <- predict_binary_model(fit_bundle, test_df, outcome, valid_predictors, categorical_predictors)
      test_actual <- ifelse(test_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)
      test_dca_rows <- compute_dca_rows(test_actual, test_probability, thresholds)
      has_test <- TRUE

      if (nzchar(test_plot_path) && test_plot_path != "NA") {
        test_plot_obj <- make_dca_plot(test_dca_rows, "Test set")
        open_png_device(test_plot_path, width = 2400, height = 1600, res = 300)
        tryCatch(
          {
            print(test_plot_obj)
          },
          finally = {
            grDevices::dev.off()
          }
        )
        if (nzchar(test_plot_pdf_path) && test_plot_pdf_path != "NA") {
          ggsave(test_plot_pdf_path, test_plot_obj, width = 7.6, height = 5.3, device = cairo_pdf)
        }
      }
    }
  }
}

result <- list(
  dataset_name = dataset_name,
  model_type = model_type,
  has_test = has_test,
  threshold_min = threshold_range[1],
  threshold_max = threshold_range[2],
  threshold_step = step_value,
  train_dca_rows = train_dca_rows,
  test_dca_rows = test_dca_rows,
  note = if (has_test) {
    paste0("DCA 已基于训练集与测试集完成，阈值范围为 ", formatC(threshold_range[1], format = "f", digits = 2), " - ", formatC(threshold_range[2], format = "f", digits = 2), "。")
  } else {
    paste0("DCA 已基于训练集完成，阈值范围为 ", formatC(threshold_range[1], format = "f", digits = 2), " - ", formatC(threshold_range[2], format = "f", digits = 2), "。")
  }
)

jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")

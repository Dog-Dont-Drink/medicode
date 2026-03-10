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
ensure_package("rms")
library(jsonlite)
suppressPackageStartupMessages(library(rms))

fit_binary_model <- function(model_type, train_df, outcome, predictors, categorical_predictors, params) {
  if (model_type == "logistic") {
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(
      model_type = model_type,
      model = stats::glm(stats::as.formula(formula_text), data = train_df, family = stats::binomial()),
      train_df = train_df
    ))
  }
  if (model_type == "random-forest") {
    ensure_package("randomForest")
    suppressPackageStartupMessages(library(randomForest))
    trees_value <- if (!is.null(params$trees)) as.integer(params$trees) else 500L
    mtry_value <- parse_mtry_arg(if (!is.null(params$mtry)) params$mtry else "sqrt(p)", length(predictors))
    seed_value <- if (!is.null(params$seed)) as.integer(params$seed) else 2026L
    set.seed(seed_value)
    formula_text <- paste(backtick(outcome), "~", paste(vapply(predictors, backtick, character(1)), collapse = " + "))
    return(list(
      model_type = model_type,
      model = randomForest::randomForest(stats::as.formula(formula_text), data = train_df, ntree = trees_value, mtry = mtry_value, importance = TRUE),
      train_df = train_df
    ))
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
  stop("校准曲线暂不支持当前模型类型。", call. = FALSE)
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
  stop("校准曲线暂不支持当前模型类型。", call. = FALSE)
}

extract_cal_metrics <- function(cal_result) {
  if (is.null(cal_result)) {
    return(list(
      c_index = NA_real_, dxy = NA_real_, intercept = NA_real_,
      slope = NA_real_, emax = NA_real_, eavg = NA_real_,
      brier = NA_real_, r2 = NA_real_
    ))
  }
  nms <- names(cal_result)
  safe_get <- function(key) {
    if (key %in% nms) as.numeric(cal_result[key]) else NA_real_
  }
  list(
    c_index = safe_get("C (ROC)"),
    dxy = safe_get("Dxy"),
    intercept = safe_get("Intercept"),
    slope = safe_get("Slope"),
    emax = safe_get("Emax"),
    eavg = safe_get("Eavg"),
    brier = safe_get("Brier"),
    r2 = safe_get("R2")
  )
}

generate_cal_plot <- function(probability, actual, png_path, pdf_path, title_label) {
  clipped <- pmin(pmax(probability, 1e-6), 1 - 1e-6)
  n <- length(clipped)
  m_value <- max(10L, min(50L, as.integer(n / 5)))

  png(filename = png_path, width = 2200, height = 1800, res = 300)
  cal_result <- tryCatch({
    result <- rms::val.prob(clipped, actual, m = m_value, cex = 0.5)
    title(main = title_label)
    result
  }, error = function(e) {
    message("val.prob PNG failed: ", e$message)
    plot.new()
    title(main = title_label)
    text(0.5, 0.5, paste("Calibration error:", e$message), cex = 0.7)
    NULL
  })
  dev.off()

  if (!is.null(cal_result)) {
    cairo_pdf(filename = pdf_path, width = 7.2, height = 5.8)
    tryCatch({
      rms::val.prob(clipped, actual, m = m_value, cex = 0.5)
      title(main = title_label)
    }, error = function(e) {
      message("val.prob PDF failed: ", e$message)
      plot.new()
      title(main = title_label)
      text(0.5, 0.5, paste("PDF error:", e$message), cex = 0.7)
    })
    dev.off()
  }

  return(cal_result)
}

# =====================================================
# Main logic wrapped in tryCatch to ALWAYS write JSON
# =====================================================
main_error <- NULL
train_metrics <- list(c_index=NA_real_, dxy=NA_real_, intercept=NA_real_, slope=NA_real_, emax=NA_real_, eavg=NA_real_, brier=NA_real_, r2=NA_real_)
test_metrics <- NULL
has_test <- FALSE

tryCatch({

  # --- Data loading ---
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
    stop("校准曲线无可用预测变量。", call. = FALSE)
  }

  eval_df <- NULL
  if (nzchar(test_csv) && test_csv != "NA" && file.exists(test_csv)) {
    raw_test <- read.csv(test_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
    raw_test <- trim_dataframe_strings(raw_test)
    if (all(columns %in% names(raw_test))) {
      candidate_test <- raw_test[stats::complete.cases(raw_test[, columns, drop = FALSE]), columns, drop = FALSE]
      if (nrow(candidate_test) > 0) {
        eval_info <- prepare_binary_outcome(candidate_test, outcome)
        eval_df <- eval_info$data
        has_test <- TRUE
      }
    }
  }

  # --- Fit model and predict ---
  fit_bundle <- fit_binary_model(model_type, train_df, outcome, valid_predictors, categorical_predictors, model_params)

  train_probability <- predict_binary_model(fit_bundle, train_df, outcome, valid_predictors, categorical_predictors)
  train_actual <- ifelse(train_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)

  # --- Train calibration plot + metrics ---
  train_cal <- generate_cal_plot(train_probability, train_actual, train_plot_path, train_plot_pdf_path, "Calibration Curve (Training Set)")
  train_metrics <- extract_cal_metrics(train_cal)

  # --- Test calibration plot + metrics (if test data exists) ---
  if (has_test && !is.null(eval_df)) {
    test_probability <- predict_binary_model(fit_bundle, eval_df, outcome, valid_predictors, categorical_predictors)
    test_actual <- ifelse(eval_df[[outcome]] == levels(train_df[[outcome]])[2], 1, 0)
    test_cal <- generate_cal_plot(test_probability, test_actual, test_plot_path, test_plot_pdf_path, "Calibration Curve (Test Set)")
    test_metrics <- extract_cal_metrics(test_cal)
  }

}, error = function(e) {
  main_error <<- e$message
  message("calibration_validation.R main error: ", e$message)
})

# --- Build note (ALWAYS runs) ---
fmt <- function(v) if (is.null(v) || is.na(v)) "NA" else formatC(v, format = "f", digits = 3)
note_parts <- paste0(
  "训练集: Slope=", fmt(train_metrics$slope), ", Intercept=", fmt(train_metrics$intercept),
  ", Brier=", fmt(train_metrics$brier), ", C-index=", fmt(train_metrics$c_index)
)
if (!is.null(test_metrics)) {
  note_parts <- paste0(note_parts, "；测试集: Slope=", fmt(test_metrics$slope),
    ", Intercept=", fmt(test_metrics$intercept), ", Brier=", fmt(test_metrics$brier),
    ", C-index=", fmt(test_metrics$c_index))
}
if (!is.null(main_error)) {
  note_parts <- paste0("执行异常: ", main_error, "。", note_parts)
}

result <- list(
  dataset_name = dataset_name,
  model_type = model_type,
  has_test = has_test,
  train_metrics = train_metrics,
  test_metrics = test_metrics,
  note = paste0(note_parts, "。")
)

# JSON is ALWAYS written, even if main logic fails
jsonlite::write_json(result, output_json, auto_unbox = TRUE, digits = 8, pretty = TRUE, null = "null")

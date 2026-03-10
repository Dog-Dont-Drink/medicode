args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_json <- args[2]
plot_forest_path <- args[3]
plot_forest_pdf_path <- args[4]
dataset_name <- args[5]
time_var <- args[6]
event_var <- args[7]
predictors <- unlist(jsonlite::fromJSON(args[8]))
categorical_predictors <- unlist(jsonlite::fromJSON(args[9]))
alpha_value <- as.numeric(args[10])
screening_mode <- if (length(args) >= 11) args[11] else "internal"
screening_threshold_arg <- if (length(args) >= 12) args[12] else "0.1"

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
ensure_package("survival")
ensure_package("ggplot2")
library(jsonlite)
library(survival)
library(ggplot2)

df <- read.csv(input_csv, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")

for (column_name in names(df)) {
  if (is.character(df[[column_name]])) {
    trimmed <- trimws(df[[column_name]])
    trimmed[trimmed == ""] <- NA
    df[[column_name]] <- trimmed
  }
}

complete_df <- df[stats::complete.cases(df[, c(time_var, event_var, predictors), drop = FALSE]), c(time_var, event_var, predictors), drop = FALSE]
excluded_rows <- nrow(df) - nrow(complete_df)
if (nrow(complete_df) < 10) {
  stop("有效样本量不足，Cox 生存分析至少需要 10 行完整观测。", call. = FALSE)
}

complete_df[[time_var]] <- suppressWarnings(as.numeric(complete_df[[time_var]]))
if (any(is.na(complete_df[[time_var]]))) {
  stop("生存时间变量必须是数值型。", call. = FALSE)
}
if (any(complete_df[[time_var]] <= 0)) {
  stop("生存时间变量必须大于 0。", call. = FALSE)
}

event_values <- unique(complete_df[[event_var]])
event_values <- event_values[!is.na(event_values)]
if (length(event_values) != 2) {
  stop("结局事件变量必须是二分类变量。", call. = FALSE)
}

if (is.numeric(complete_df[[event_var]])) {
  numeric_values <- sort(unique(as.numeric(complete_df[[event_var]])))
  if (!all(numeric_values %in% c(0, 1))) {
    stop("数值型事件变量仅支持 0/1 编码。", call. = FALSE)
  }
  reference_level <- "0"
  event_level <- "1"
  complete_df$event_status <- as.numeric(complete_df[[event_var]])
} else {
  complete_df[[event_var]] <- factor(complete_df[[event_var]])
  if (nlevels(complete_df[[event_var]]) != 2) {
    stop("结局事件变量必须恰好有两个水平。", call. = FALSE)
  }
  reference_level <- levels(complete_df[[event_var]])[1]
  event_level <- levels(complete_df[[event_var]])[2]
  complete_df$event_status <- ifelse(complete_df[[event_var]] == event_level, 1, 0)
}

if (!any(complete_df$event_status == 1)) {
  stop("当前完整记录中没有事件发生，无法执行 Cox 生存分析。", call. = FALSE)
}
if (!any(complete_df$event_status == 0)) {
  stop("当前完整记录中没有删失样本，无法执行 Cox 生存分析。", call. = FALSE)
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

extract_cox_rows <- function(formula_text, data) {
  fit <- survival::coxph(stats::as.formula(formula_text), data = data, x = TRUE, model = TRUE)
  fit_summary <- summary(fit)
  coef_matrix <- fit_summary$coefficients
  conf_matrix <- fit_summary$conf.int
  data.frame(
    term = rownames(coef_matrix),
    coefficient = unname(coef_matrix[, "coef"]),
    hazard_ratio = unname(conf_matrix[, "exp(coef)"]),
    std_error = unname(coef_matrix[, "se(coef)"]),
    z_value = unname(coef_matrix[, "z"]),
    p_value = unname(coef_matrix[, "Pr(>|z|)"]),
    conf_low = unname(conf_matrix[, "lower .95"]),
    conf_high = unname(conf_matrix[, "upper .95"]),
    check.names = FALSE
  )
}

univariate_rows <- data.frame(
  term = character(0),
  hazard_ratio = numeric(0),
  std_error = numeric(0),
  z_value = numeric(0),
  p_value = numeric(0),
  conf_low = numeric(0),
  conf_high = numeric(0),
  check.names = FALSE
)
screened_predictors <- c()
for (predictor in valid_predictors) {
  predictor_formula <- paste0("survival::Surv(", backtick(time_var), ", event_status) ~ ", backtick(predictor))
  predictor_rows <- tryCatch(
    extract_cox_rows(predictor_formula, complete_df),
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
    stop("单因素分析后没有变量满足 P < 0.1，无法进入多因素 Cox 回归。", call. = FALSE)
  }
}

formula_text <- paste0("survival::Surv(", backtick(time_var), ", event_status) ~ ", paste(vapply(screened_predictors, backtick, character(1)), collapse = " + "))
fit <- survival::coxph(stats::as.formula(formula_text), data = complete_df, x = TRUE, model = TRUE)
fit_summary <- summary(fit)
coef_df <- extract_cox_rows(formula_text, complete_df)

ph_global_p <- NA_real_
ph_rows <- data.frame(term = character(0), statistic = numeric(0), df = numeric(0), p_value = numeric(0), stringsAsFactors = FALSE)
ph_note <- "比例风险假设检验未执行"
ph_result <- tryCatch(survival::cox.zph(fit, transform = "km"), error = function(e) NULL)
if (!is.null(ph_result)) {
  ph_table <- as.data.frame(ph_result$table)
  ph_table$term <- rownames(ph_table)
  if ("GLOBAL" %in% ph_table$term) {
    ph_global_p <- ph_table[ph_table$term == "GLOBAL", "p"][1]
    ph_rows <- ph_table[ph_table$term != "GLOBAL", c("term", "chisq", "df", "p"), drop = FALSE]
    colnames(ph_rows) <- c("term", "statistic", "df", "p_value")
  } else {
    ph_rows <- ph_table[, c("term", "chisq", "df", "p"), drop = FALSE]
    colnames(ph_rows) <- c("term", "statistic", "df", "p_value")
  }
  ph_note <- if (is.na(ph_global_p)) "cox.zph 已执行，但未返回全局 P 值。" else paste0("Schoenfeld 残差全局检验 P=", formatC(ph_global_p, format = "f", digits = 3))
}

concordance_value <- NA_real_
concordance_se <- NA_real_
if (!is.null(fit_summary$concordance) && length(fit_summary$concordance) >= 2) {
  concordance_value <- unname(fit_summary$concordance[1])
  concordance_se <- unname(fit_summary$concordance[2])
}

logtest <- fit_summary$logtest
waldtest <- fit_summary$waldtest
sctest <- fit_summary$sctest

result <- list(
  dataset_name = dataset_name,
  time_variable = time_var,
  event_variable = event_var,
  event_level = event_level,
  reference_level = reference_level,
  predictor_variables = screened_predictors,
  sample_size = nrow(complete_df),
  event_count = sum(complete_df$event_status == 1),
  excluded_rows = excluded_rows,
  alpha = alpha_value,
  concordance = concordance_value,
  concordance_std_error = concordance_se,
  likelihood_ratio_statistic = if (is.null(logtest)) NA_real_ else unname(logtest[1]),
  likelihood_ratio_df = if (is.null(logtest)) NA_real_ else unname(logtest[2]),
  likelihood_ratio_p_value = if (is.null(logtest)) NA_real_ else unname(logtest[3]),
  wald_statistic = if (is.null(waldtest)) NA_real_ else unname(waldtest[1]),
  wald_df = if (is.null(waldtest)) NA_real_ else unname(waldtest[2]),
  wald_p_value = if (is.null(waldtest)) NA_real_ else unname(waldtest[3]),
  score_statistic = if (is.null(sctest)) NA_real_ else unname(sctest[1]),
  score_df = if (is.null(sctest)) NA_real_ else unname(sctest[2]),
  score_p_value = if (is.null(sctest)) NA_real_ else unname(sctest[3]),
  global_ph_p_value = ph_global_p,
  formula = formula_text,
  assumptions = list(
    "生存时间变量必须为连续正数，事件变量必须为二分类变量。",
    "模型默认使用完整案例进行拟合，含缺失值的记录已剔除。",
    "HR > 1 表示事件风险升高，HR < 1 表示事件风险降低。",
    if (screening_mode == "internal") {
      paste0("先进行单因素 Cox 回归筛选，P < ", screening_p_threshold, " 的变量纳入多因素模型。")
    } else {
      "当前工作流已提供上游筛选变量集，多因素模型直接使用输入变量建模。"
    },
    ph_note
  ),
  univariate_coefficients = univariate_rows,
  coefficients = coef_df,
  proportional_hazards_tests = ph_rows,
  note = paste0(
    "事件水平设为 ", event_level, "，参考水平为 ", reference_level,
    "；完整样本中共观察到 ", sum(complete_df$event_status == 1), " 个事件；",
    if (screening_mode == "internal") paste0("单因素 P < ", screening_p_threshold, " 纳入多因素分析；") else "已直接使用上游筛选变量；",
    "入模变量：", paste(screened_predictors, collapse = ", "), "。"
  )
)

p <- NULL
png(filename = plot_forest_path, width = 2400, height = max(980, 360 + 102 * nrow(coef_df)), res = 300)
tryCatch({
  plot_df <- coef_df
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

  p <- ggplot(plot_df, aes(x = hazard_ratio, y = term_label)) +
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
      x = "Hazard ratio",
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
  height = max(5.3, 2.35 + 0.17 * nrow(coef_df)),
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

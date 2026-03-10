args <- commandArgs(trailingOnly = TRUE)
input_csv <- args[1]
output_csv <- args[2]
output_json <- args[3]
dataset_name <- args[4]
method <- args[5]
threshold_arg <- args[6]
analysis_columns <- unlist(jsonlite::fromJSON(args[7]))
protected_columns <- unlist(jsonlite::fromJSON(args[8]))

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
library(jsonlite)

threshold <- suppressWarnings(as.numeric(threshold_arg))
if (is.na(threshold) || threshold < 0 || threshold > 1) {
  stop("缺失比例阈值必须介于 0 和 1 之间。", call. = FALSE)
}

if (method == "多重插补") {
  ensure_package("mice")
}

df <- read.csv(
  input_csv,
  check.names = FALSE,
  stringsAsFactors = FALSE,
  fileEncoding = "UTF-8-BOM",
  na.strings = c("", "NA", "NaN")
)

trim_empty_to_na <- function(x) {
  if (is.character(x)) {
    x <- trimws(x)
    x[x == ""] <- NA
  }
  x
}

for (column_name in names(df)) {
  df[[column_name]] <- trim_empty_to_na(df[[column_name]])
}

input_rows <- nrow(df)
input_columns <- ncol(df)

available_columns <- intersect(analysis_columns, names(df))
if (length(available_columns) == 0) {
  available_columns <- names(df)
}

protected_columns <- intersect(protected_columns, available_columns)
droppable_columns <- setdiff(available_columns, protected_columns)

missing_rates <- vapply(
  available_columns,
  function(column_name) mean(is.na(df[[column_name]])),
  numeric(1)
)

drop_columns <- unique(c(
  names(missing_rates)[missing_rates > threshold & names(missing_rates) %in% droppable_columns],
  droppable_columns[vapply(droppable_columns, function(column_name) all(is.na(df[[column_name]])), logical(1))]
))

working_df <- df
if (length(drop_columns) > 0) {
  working_df <- working_df[, setdiff(names(working_df), drop_columns), drop = FALSE]
}

processed_columns <- intersect(available_columns, names(working_df))
if (length(processed_columns) == 0) {
  stop("缺失值处理后没有可继续分析的字段，请降低阈值或重新选择字段。", call. = FALSE)
}

missing_cells_before <- sum(is.na(working_df[, processed_columns, drop = FALSE]))
numeric_columns <- processed_columns[vapply(working_df[, processed_columns, drop = FALSE], is.numeric, logical(1))]
categorical_columns <- setdiff(processed_columns, numeric_columns)
numeric_imputed_cells <- sum(is.na(working_df[, numeric_columns, drop = FALSE]))
categorical_imputed_cells <- sum(is.na(working_df[, categorical_columns, drop = FALSE]))
operations <- c()

mode_fill <- function(x) {
  values <- x[!is.na(x)]
  if (length(values) == 0) {
    return("Unknown")
  }
  as.character(names(sort(table(values), decreasing = TRUE)[1]))
}

if (method == "删除缺失") {
  keep_mask <- stats::complete.cases(working_df[, processed_columns, drop = FALSE])
  removed_rows <- sum(!keep_mask)
  working_df <- working_df[keep_mask, , drop = FALSE]
  operations <- c(operations, if (removed_rows > 0) {
    paste0("按分析字段删除含缺失观测 ", removed_rows, " 行。")
  } else {
    "分析字段无缺失，未删除任何观测。"
  })
} else if (method == "均值/众数插补") {
  for (column_name in numeric_columns) {
    if (anyNA(working_df[[column_name]])) {
      fill_value <- mean(working_df[[column_name]], na.rm = TRUE)
      if (is.nan(fill_value)) fill_value <- 0
      working_df[[column_name]][is.na(working_df[[column_name]])] <- fill_value
    }
  }
  for (column_name in categorical_columns) {
    if (anyNA(working_df[[column_name]])) {
      fill_value <- mode_fill(working_df[[column_name]])
      working_df[[column_name]][is.na(working_df[[column_name]])] <- fill_value
    }
  }
  operations <- c(operations, "已执行均值/众数插补。")
} else if (method == "多重插补") {
  impute_df <- working_df[, processed_columns, drop = FALSE]
  for (column_name in categorical_columns) {
    impute_df[[column_name]] <- as.factor(impute_df[[column_name]])
  }
  methods <- mice::make.method(impute_df)
  predictor_matrix <- mice::make.predictorMatrix(impute_df)
  diag(predictor_matrix) <- 0
  for (column_name in processed_columns) {
    if (!anyNA(impute_df[[column_name]])) {
      methods[column_name] <- ""
    }
  }
  imputed <- suppressWarnings(
    mice::mice(
      impute_df,
      m = 5,
      maxit = 5,
      seed = 2026,
      method = methods,
      predictorMatrix = predictor_matrix,
      printFlag = FALSE
    )
  )
  completed <- mice::complete(imputed, 1)
  for (column_name in processed_columns) {
    working_df[[column_name]] <- completed[[column_name]]
  }
  operations <- c(operations, "已执行 mice 多重插补。")
}

if (length(drop_columns) > 0) {
  operations <- c(operations, paste0("缺失比例超过阈值的字段已移除: ", paste(drop_columns, collapse = ", "), "。"))
}

missing_cells_after <- sum(is.na(working_df[, processed_columns, drop = FALSE]))
output_rows <- nrow(working_df)
output_columns <- ncol(working_df)
removed_rows <- input_rows - output_rows
removed_columns <- input_columns - output_columns
output_name <- paste0(tools::file_path_sans_ext(dataset_name), "_missing_processed.csv")

write.csv(working_df, output_csv, row.names = FALSE, fileEncoding = "UTF-8")

result <- list(
  dataset_name = dataset_name,
  method = method,
  threshold = threshold,
  input_rows = input_rows,
  input_columns = input_columns,
  output_rows = output_rows,
  output_columns = output_columns,
  removed_rows = removed_rows,
  removed_columns = removed_columns,
  removed_column_names = drop_columns,
  numeric_imputed_cells = numeric_imputed_cells,
  categorical_imputed_cells = categorical_imputed_cells,
  missing_cells_before = missing_cells_before,
  missing_cells_after = missing_cells_after,
  processed_columns = processed_columns,
  output_name = output_name,
  operations = operations
)

write_json(result, output_json, auto_unbox = TRUE, pretty = TRUE, na = "null")

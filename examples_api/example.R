#' Download tree metadata and tree point clouds from PyTreeDB
#'
#' @param pcMode Source of the point cloud. Can be TLS, ULS, or ALS
#' @param species Species name in Latin
#' @param minHeight Minimum tree height
#' @param maxHeight Maximum tree height
#' @param minDBH Minimum diameter at breast height
#' @param maxDBH Maximum diameter at breast height
#' @param dataSource Source of the measurements. Can be TLS, ULS, ALS, or FI (forest inventory)
#' @param minCD Minimum crown diameter
#' @param maxCD Maximum crown diameter
#' @param minCBH Minimum crown base height defined by lowest branch
#' @param maxCBH Maximum crown base height defined by lowest branch
#' @param minCBHgreen Minimum crown base height defined by lowest green (living branch)
#' @param maxCBHgreen Maximum crown base height defined by lowest green (living branch)
#' @param canopyCondition Canopy condition of deciduous trees at acquisition time. Can be leaf-on or leaf-off #' @param pcQuality Quality of the segmented point cloud. Can be 1 (very good), 2, 3, 4, 5, 6 (very poor). Given as vector of one or more values.
#' @param outPath Name of the directory where the downloaded data should be saved
#' @param outFileName Name of the file where the tree metadata should be saved. If outFileName = NA, no file will be saved.
#' @param downloadPC Parameter indicating if tree point clouds should be saved. Can be TRUE or FALSE.
#'
#' @return Tree metadata as data.frame
#' @export  . Tree point clouds (as .laz files) and tree metadata (as .csv file)
#'
#' @examples
#' getTrees(pcMode = "ULS", species = "Quercus robur", minHeight = 2, maxHeight = 40.0, minDBH = 5.0, maxDBH = 100.0, dataSource = "ULS", minCD = NA, maxCD = NA, minCBH = NA, maxCBH = NA, minCBHgreen = NA, maxCBHgreen = NA, canopyCondition = "leaf-on", pcQuality = c(1, 2, 3), outPath = "DownloadPyTreeDB", outFileName = "treeInfo.csv", downloadPC = TRUE)
#' 
#'
getTrees <- function(pcMode, species, minHeight = NA, maxHeight = NA, minDBH = NA, maxDBH = NA, dataSource, minCD = NA, maxCD = NA, minCBH = NA, maxCBH = NA, minCBHgreen = NA, maxCBHgreen = NA, canopyCondition, pcQuality, outPath = NA, outFileName = NA, downloadPC = NA){
  require(httr)
  require(jsonlite)
  require(data.table)
  
  #### Request data ####
  query <- paste0("{\"properties.data.mode\" : \"", pcMode, "\"", ", \"properties.species\" : \"", species, "\"",
                  ", \"properties.data.canopy_condition\" : \"", canopyCondition, "\"}")
  req <- list(query = c(query))                      
  
  res <- POST("http://syssifoss.geog.uni-heidelberg.de:5001/search", body = req, encode="form")
  
  data = fromJSON(rawToChar(res$content))
  
  #### Filter data for required measurements ####
  measurements0 <- data$query$properties$measurements
  ids <- data$query$properties$id
  measurements1 <- mapply(cbind, measurements0, "id"=ids, SIMPLIFY=F)
  
  measurements <- rbindlist(measurements1, fill = T)
  
  minHeight <-  ifelse(is.na(minHeight), 0, minHeight)
  minDBH <-  ifelse(is.na(minDBH), 0, minDBH)
  minCBH <- ifelse(is.na(minCBH), 0, minCBH)
  minCBHgreen <- ifelse(is.na(minCBHgreen), 0, minCBHgreen)
  minCD <- ifelse(is.na(minCD), 0, minCD)
  
  maxHeight <-  ifelse(is.na(maxHeight), 999, maxHeight)
  maxDBH <-  ifelse(is.na(maxDBH), 999, maxDBH)
  maxCBH <- ifelse(is.na(maxCBH), 999, maxCBH)
  maxCBHgreen <- ifelse(is.na(maxCBHgreen), 999, maxCBHgreen)
  maxCD <- ifelse(is.na(maxCD), 999, maxCD)
  
  meas <- measurements[((height_m >= minHeight &  height_m <= maxHeight) | is.na(height_m)) &  source == dataSource & ((mean_crown_diameter_m >= minCD &  mean_crown_diameter_m <= maxCD) | is.na(mean_crown_diameter_m)) & ((DBH_cm >= minDBH &  DBH_cm <= maxDBH) | is.na(DBH_cm)) & ((crown_base_height_m >= minCBH &  crown_base_height_m <= maxCBH) | is.na(crown_base_height_m)) & ((crown_base_height_green_m >= minCBHgreen &  crown_base_height_green_m <= maxCBHgreen) | is.na(crown_base_height_green_m)), ]
  
 #### Filter data for required properties ####
  properties0 <- data$query$properties$data
  properties1 <- mapply(cbind, properties0, "id"=ids, SIMPLIFY=F)
  
  properties <- rbindlist(properties1, fill = T)
  
  prop <- properties[quality %in% pcQuality & mode == pcMode & canopy_condition == canopyCondition, ]
  
  #### Merge output ####
  out <- merge(prop[, -c("date", "crs", "canopy_condition")], meas[, -c("crs", "position_xyz")], by = "id", all.x = F, all.y = F)
  
  #### Save metadata and download point clouds ####
  if(!is.na(outFileName)){fwrite(out, paste0(outPath, "/", outFileName))}
  
  if(downloadPC){
    lazFiles <- out$file
    for(i1 in 1:length(lazFiles)){
      lazName <- strsplit(lazFiles[i1], "/")[[1]][5]
      if(is.na(outPath)){outPath <- "."}
      download.file(lazFiles[i1], paste0(outPath, "/", lazName), mode = "wb")
    }  
  }
  
 return(out)
}
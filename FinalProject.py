#-------------------------------------------------------------------------------
# Name:        completed processing files and in gdb
# Purpose:
#
# Author:      Becky
#
# Created:     05-04-2025
# Copyright:   (c) Becky 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#import the ArcPy Module
import os
import shutil
import arcpy
from arcpy.sa import *

#define base workspace
base_folder = r"C:\GEOS456\FinalProject"
arcpy.env.workspace = base_folder
arcpy.env.overwriteOutput = True

#add messages() after each tool if you'd like it to include messages
def messages():
    print("Processing...")
    print(arcpy.GetMessage(0))
    count = arcpy.GetMessageCount()
    print(arcpy.GetMessage(count-1))

#create fresh temp folder
temp_folder = os.path.join(base_folder, "temp")
if os.path.exists(temp_folder):
    shutil.rmtree(temp_folder, ignore_errors=True)
os.makedirs(temp_folder)
print("Temp data will be deleted if it already exists and then created afresh.")

#create or replace geodatabase
gdb_path = os.path.join(base_folder, "KananaskisWildlife.gdb")
if arcpy.Exists(gdb_path):
    print("The gdb already exists and will be deleted, then created afresh.")
    arcpy.management.Delete(gdb_path)
    messages()
arcpy.management.CreateFileGDB(out_folder_path=base_folder, out_name="KananaskisWildlife.gdb")
print("Geodatabase created.")
messages()

#check out spatial analyst extension
arcpy.CheckOutExtension("Spatial")
print("Spatial Extension Engaged!")

#create a list of all the original data features stored in the folder
folders = [
    r"C:\GEOS456\FinalProject\ATS",
    r"C:\GEOS456\FinalProject\dem",
    r"C:\GEOS456\FinalProject\Kananaskis",
    r"C:\GEOS456\FinalProject\Landcover",
    r"C:\GEOS456\FinalProject\NTS\NTS-50",
    r"C:\GEOS456\FinalProject\Wildlife"]

#set up dictionary for solving raster naming problem (the names were getting too long and throwing errors, and I hate
#typing out Kananaskis)
folder_prefixes = {
    r"C:\GEOS456\FinalProject\ATS": "A",
    r"C:\GEOS456\FinalProject\dem": "D",
    r"C:\GEOS456\FinalProject\Kananaskis": "K",
    r"C:\GEOS456\FinalProject\Landcover": "L",
    r"C:\GEOS456\FinalProject\NTS\NTS-50": "N",
    r"C:\GEOS456\FinalProject\Wildlife": "W"
}



def clean_name(name):
    name = os.path.splitext(name)[0]
    name = name.replace("-", "_").replace(" ", "_")
    return name[:13]

target_sr = arcpy.SpatialReference(26911)  # NAD83 UTM Zone 11N

#loop through folders

for folder in folders:
    arcpy.env.workspace = folder
    prefix = folder_prefixes[folder]

    print(f"\nProcessing folder: {folder} | Prefix: {prefix}")

    for fc in arcpy.ListFeatureClasses() or []:
        input_fc = os.path.join(folder, fc)
        desc = arcpy.Describe(input_fc)

        print(f"Name: {fc}")
        print(f"  Shape Type: {desc.shapeType}")
        print(f"  Spatial Ref Name: {desc.spatialReference.name}")
        print(f"  Spatial Ref Type: {desc.spatialReference.type}")

        #handle Landcover specially
        if "Landcover" in folder:
            projected_fc = os.path.join(temp_folder, "landcover_projected")
            clipped_fc = os.path.join(temp_folder, "landcover_clipped")

            print(f"Projecting Landcover: {fc} -> {projected_fc}")
            arcpy.management.Project(input_fc, projected_fc, target_sr)
            messages()

            print(f"Clipping Landcover to StudyArea -> {clipped_fc}")
            clip_mask = r"C:\GEOS456\FinalProject\Kananaskis\KCountry_Bound.shp"
            arcpy.analysis.Clip(projected_fc, clip_mask, clipped_fc)
            messages()

            print(f"Converting Landcover to raster")
            raster_output = os.path.join(temp_folder, "LandcoverR")
            arcpy.conversion.PolygonToRaster(
            in_features=clipped_fc,
            value_field="LC_class",
            out_rasterdataset=raster_output,
            cell_assignment="MAXIMUM_COMBINED_AREA",
            priority_field="",
            cellsize=25
        )

            messages()
            arcpy.management.BuildRasterAttributeTable(raster_output, "OVERWRITE")
            Landcover_Reclass = Reclassify(raster_output, "Value", "20 10; 31 8; 32 7; 33 6; 34 10; 50 3; 110 2; 120 9; 210 1; 220 1; 230 1")
            messages()
            print("Landcover misery has been dealt with. Your processor chip is smokin'.")
            reclass_output = os.path.join(gdb_path, "Landcover")
            Landcover_Reclass.save(reclass_output)
            messages()
            print("Fancy pants raster with reclassification has been saved to the geodatabase. And there was much rejoicing. Yay.")
            print("")
            continue  # skip rest of loop for Landcover

        #for other feature classes
        out_name = clean_name(f"{prefix}_{fc}")
        #check if needing projection change

        if desc.spatialReference.name != target_sr.name:
            print(f"Reprojecting feature class: {fc} -> {out_name}")
            projected_fc = os.path.join(temp_folder, f"{prefix}_{fc}_proj")
            arcpy.management.Project(input_fc, projected_fc, target_sr)
            messages()
        else:
            projected_fc = input_fc
        messages()

        #clip to study area
        clip_boundary = r"C:\GEOS456\FinalProject\Kananaskis\KCountry_Bound.shp"  # study area, doens't need to have projection changed since already in NAD83 UTM Zone 11N
        clipped_fc = os.path.join(temp_folder, f"{out_name}_clip")
        print(f"Clipping feature class to study area: {fc} -> {out_name}")
        arcpy.analysis.Clip(projected_fc, clip_boundary, clipped_fc)
        messages()

        #save clipped to gdb
        arcpy.management.CopyFeatures(clipped_fc, os.path.join(gdb_path, out_name))
        messages()
    #raster processing
    for raster in arcpy.ListRasters() or []:
        input_raster = os.path.join(folder, raster)
        desc = arcpy.Describe(input_raster)

        print(f"Name: {raster}")
        print(f"  Raster Format: {desc.format}")
        print(f"  Data Type: {desc.datasetType}")
        print(f"  Pixel Type: {desc.pixelType}")
        print(f"  Spatial Ref Name: {desc.spatialReference.name}")
        print(f"  Spatial Ref Type: {desc.spatialReference.type}")
        print(f"  Cell Size (X, Y): ({desc.meanCellWidth}, {desc.meanCellHeight})")

        base_name = clean_name(f"{prefix}_{raster}")
        projected_raster = os.path.join(temp_folder, f"p_{base_name}")
        clipped_raster = os.path.join(temp_folder, f"c_{base_name}")
        final_output = os.path.join(gdb_path, base_name)

        if desc.spatialReference.name != target_sr.name:
            print(f"Reprojecting raster: {raster} -> {projected_raster}")
            arcpy.management.ProjectRaster(input_raster, projected_raster, target_sr)
            messages()
            working_raster = projected_raster
        else:
            print(f"Copying raster (same projection) to temp: {raster} -> {projected_raster}")
            arcpy.management.CopyRaster(input_raster, projected_raster)
            messages()
            working_raster = projected_raster

        print(f"Clipping raster to study area: {working_raster} -> {clipped_raster}")
        clip_mask = r"C:\GEOS456\FinalProject\Kananaskis\KCountry_Bound.shp"
        arcpy.sa.ExtractByMask(working_raster, clip_mask).save(clipped_raster)
        messages()

        print(f"Saving final raster to gdb: {clipped_raster} -> {final_output}")
        arcpy.management.CopyRaster(clipped_raster, final_output)
        messages()

        arcpy.management.Delete(projected_raster)
        arcpy.management.Delete(clipped_raster)

print("All data processed and organized.")
print("")

print("For nosy folks who want to know the 1:50,000 NTS map sheets and the TWP-TGE-MER that covers the park, hold onto your socks...")

arcpy.env.workspace = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"
arcpy.env.overwriteOutput = True
nts_fc = "N_NTS50"
townships_fc = "A_AB_Township"

#Make township layer
arcpy.MakeFeatureLayer_management(townships_fc, "twp_lyr")

#Cursor through each NTS tile
with arcpy.da.SearchCursor(nts_fc, ["NAME", "SHAPE@"]) as nts_cursor:
    for nts_row in nts_cursor:
        nts_id = nts_row[0]
        nts_geom = nts_row[1]

        if not nts_geom:
            continue

        # Create temporary layer for the current NTS tile geometry
        arcpy.MakeFeatureLayer_management(nts_fc, "temp_nts", f"NAME = '{nts_id}'")

        # Select townships that intersect this tile
        arcpy.SelectLayerByLocation_management("twp_lyr", "INTERSECT", "temp_nts")

        print(f"\nNTS Tile: {nts_id}")

        # Print selected townships
        with arcpy.da.SearchCursor("twp_lyr", ["TWP", "RGE", "M"]) as twp_cursor:
            for row in twp_cursor:
                print(f"  → TWP {row[0]}, RGE {row[1]}, MER {row[2]}")

        del twp_cursor

'''
Use the following criteria to determine the optimal routes
The lower the cost surface, the better for the optimal routes
Landcover: the more natural (with the exception of water), the lower the cost
Hydroglogy: the closer to hydrological features, the lower the cost (opposite to roads and trails)
Roads: The further away for the roads, the lower the cost - use distance accumulation for cost surface

Trails: The further away from the trails, the lower the cost - use distance accumulation for cost surface
Terrain Ruggedness: The more rugged, the lower the cost (don't have yet, need to generate)

------------------------------------------------------------------------------

The following rasters will determine whether to rescale by function or to reclassify
Landcover: discrete raster -> reclassify
Hydrology: discrete raster -> rescale by function
Roads: continuous raster -> rescale by function

Trails: continous raster -> rescale by function
Terrain Ruggedness: continous raster -> recscale by function


'''
#set raster size to standard
arcpy.env.cellSize = 25
arcpy.env.workspace =r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"

#define variables for the rasters
#the DEM will be the imputs to the creation of the terrain ruggedness raster (called ab_dem in gdb)
Elevation = arcpy.Raster("D_ab_dem")
Land_Cover = arcpy.Raster("Landcover")

#output zonal table in GDB
zonal_table = "ElevationStats_Kananaskis"
arcpy.sa.ZonalStatisticsAsTable(
    in_zone_data="K_KCountry_Bo",
    zone_field="OBJECTID",
    in_value_raster="D_ab_dem",
    out_table=zonal_table,
    statistics_type="MEAN"
)

print("Zonal statistics table created for average elevation.")

#define variables for the habitats (just simplfying the variable so you don't have to type in every time)
Habitats = "W_Bear_Habita"

#generate and save the terrain ruggedness (had to add in the if loop because issues)

Ruggedness = FocalStatistics(Elevation, NbrRectangle(3,3, "CELL"), "RANGE")
messages()

Ruggedness.save("Terrain_R")

#create and save a roads distance raster (references the Roads in the gdb)

Roads_Distance = DistanceAccumulation("K_Road")
messages()

Roads_Distance.save("Distance_to_Roads")

#create and save a trails distance raster (references Kananaskis_Tr in the gdb)

Trails_Distance = DistanceAccumulation("K_Trails")
messages()

Trails_Distance.save("Distance_to_Trails")

#create and save a water distace raster (references K_Hydro in the gdb)
Hydrology_Distance = DistanceAccumulation("K_Hydro")
messages()

Hydrology_Distance.save("Distance_to_Hydro")


#use the rescale by function to assign the classes to the continous rasters
#rescale the terrain and the roads raster
rescale_TR = RescaleByFunction(Ruggedness, "TfLarge", 10, 1)
messages()
rescale_TR.save("Terrain_Rescale")

#the inversion on the appeal of the roads is opposite terrain in the values earlier (confused? it's ok)
rescale_Roads = RescaleByFunction(Roads_Distance, "TfLarge", 10, 1)
messages()
rescale_Roads.save("Roads_Rescale")

#rescale the trails
rescale_Trails = RescaleByFunction(Trails_Distance, "TfLarge", 10, 1)
rescale_Trails.save("Trails_Rescale")

#rescale the hydrology function
rescale_Hydro = RescaleByFunction(Hydrology_Distance, "TfLarge", 10, 1)
messages()
rescale_Hydro.save("Hydrology_Rescale")

#use the reclassify to assign classes to the discrete rasters
#reclassify the landcover and protected areas (use the \ to contine the line if needed)
Land_Cover_Reclass = Reclassify(Land_Cover, "Value", "11 10; 21 8; 22 7; 23 8; 24 9; 31 6; 41 2; 42 1; 43 2; 52 3; 71 3; 81 4; 82 6; 90 4; 95 4")
messages()

Land_Cover_Reclass.save("LC_Reclass")


#combine all the rasters together using the weighted sum tool (make sure that you are selected the correct raster and each raster is in its own square bracket, separated by comma. Two square brackets at the beggining)
weighted_sum = WeightedSum(WSTable([[rescale_TR, "Value", 1], [rescale_Roads, "Value", 1], [Land_Cover_Reclass, "Value", 1], [rescale_Hydro, "Value", 1], [rescale_Trails, "Value", 1]]))
messages()

weighted_sum.save("Combined_Rasters")
print(f"Cell size (X, Y): {weighted_sum.meanCellWidth}, {weighted_sum.meanCellHeight}")


#generate the optimal routes to connect the bear habitat (vector file so you don't need to save like the rasters)
Optimal_Routes = OptimalRegionConnections(Habitats, "Paths", "", weighted_sum)
messages()

#And the chart about land cover
from arcpy.sa import *

arcpy.env.workspace = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"
arcpy.CheckOutExtension("Spatial")

# Create the table
TabulateArea(
    in_zone_data="K_KCountry_Bo",
    zone_field="OBJECTID",
    in_class_data="LC_Reclass",
    class_field="Value",
    out_table="Landcover_Area_by_Class",
    processing_cell_size=25
)

print("TabulateArea table 'Landcover_Area_by_Class' created.")
# Set workspace
arcpy.env.workspace = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"

# Your reclassified landcover labels (from scale value table)
landcover_labels = {
    1: "Coniferous / Broadleaf / Mixed Forest",
    2: "Grassland",
    3: "Shrubland",
    6: "Exposed Land",
    7: "Rock/Rubble",
    8: "Snow/Ice",
    9: "Agriculture",
    10: "Water / Developed"
}

# Source table from TabulateArea
source_table = "Landcover_Area_by_Class"
output_table = "Landcover_Area_Summary"

# Delete existing output table if it exists
if arcpy.Exists(output_table):
    arcpy.management.Delete(output_table)

# Create the new table and fields
arcpy.management.CreateTable(arcpy.env.workspace, output_table)
arcpy.management.AddField(output_table, "Landcover_Type", "TEXT", field_length=50)
arcpy.management.AddField(output_table, "Area_ha", "DOUBLE")

# Set up insert cursor
insert_fields = ["Landcover_Type", "Area_ha"]
insert_cursor = arcpy.da.InsertCursor(output_table, insert_fields)

print("\nLandcover Area Summary (in hectares):")

# Loop through VALUE_ fields in the source table
for field in arcpy.ListFields(source_table):
    if field.name.startswith("VALUE_"):
        value = int(field.name.replace("VALUE_", ""))
        label = landcover_labels.get(value, f"Class {value}")

        with arcpy.da.SearchCursor(source_table, [field.name]) as cursor:
            for row in cursor:
                area_ha = row[0] / 10000
                print(f"{label}: {area_ha:.2f} hectares")
                insert_cursor.insertRow((label, area_ha))

# Clean up cursor
del insert_cursor

print(f"\nGDB table created: {output_table}")


#let's clean up our mess and make the database look as expected
#rename dataset fc and rasters to match assignment expectations
gdb_path = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"
arcpy.env.workspace = gdb_path

print("Tidying up the database and the files before mapping because it causes issues if we do it after...")
# Define raster and feature renames separately
raster_renames = [
    ("Combined_Rasters", "OptimalRoutes"),
    ("D_ab_dem", "DEM")
]

feature_renames = [
    ("K_KCountry_Bo", "KPBoundary"),
    ("K_Road", "Roads"),
    ("K_Trails", "Trails"),
    ("K_Hydro", "Hydrology"),
    ("W_Bear_Habita", "Habitats"),
    ("W_ESA", "ESA"),
    ("A_Ab_Township", "Townships"),
    ("N_NTS50", "NTS")
]

# Safely copy and rename rasters
for old_raster, new_raster in raster_renames:
    if arcpy.Exists(old_raster):
        if arcpy.Exists(new_raster):
            arcpy.ClearWorkspaceCache_management()
            arcpy.management.Delete(new_raster)
        arcpy.management.CopyRaster(old_raster, new_raster)
        arcpy.ClearWorkspaceCache_management()
        arcpy.management.Delete(old_raster)
        print(f"Raster '{old_raster}' renamed to '{new_raster}' via copy/delete.")
    else:
        print(f"Raster '{old_raster}' not found.")
messages()
# Rename feature classes normally (still safe unless layout is using them)
for old_fc, new_fc in feature_renames:
    if arcpy.Exists(old_fc):
        if arcpy.Exists(new_fc):
            arcpy.management.Delete(new_fc)
        arcpy.management.Rename(old_fc, new_fc)
        print(f"Feature class '{old_fc}' renamed to '{new_fc}'.")
    else:
        print(f"Feature class '{old_fc}' not found.")
messages()
#removing any intermediate rasters to the temp folder
temp = r"C:\GEOS456\FinalProject\temp"
gdb_path =r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"

rasters_to_move = ["Distance_to_Roads", "Distance_to_Trails", "Distance_to_Hydro", "Terrain_Rescale", "Terrain_R", "Roads_Rescale", "Trails_Rescale", "LC_Reclass"]

for raster in rasters_to_move:
    src_path = os.path.join(gdb_path, raster)
    dst_path = os.path.join(temp, f"{raster}.tif")
    arcpy.management.CopyRaster(src_path, dst_path)
    print(f"Copied {raster} to temp folder.")

#Map this puppy out!
#import the arcpy and mapping modules (you can use any term you want but MAP signals to other readers what's happening')
import arcpy
import arcpy.mp as MAP

#set the workspace location to the gdb
arcpy.env.workspace = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"

#set the overwrite ouputs to true
arcpy.env.overwriteOutput = True

#reference the exisiting map document using the ArcGISProject() function
aprx = MAP.ArcGISProject(r"C:\GEOS456\FinalProject\GEOS456_FinalProject.aprx")

#save a copy of the original aprx (keep the file type, in this case, I added my initals)
aprx.saveACopy(r"C:\GEOS456\FinalProject\FinalProject_RRB.aprx")

#push the changes to the copy rather than the original
aprx_copy = MAP.ArcGISProject(r"C:\GEOS456\FinalProject\FinalProject_RRB.aprx")

#use the mapping module to list the map frames in the aprx
mapFrames = aprx_copy.listMaps()
for eachMap in mapFrames:
    print(eachMap.name) #provide the ability to get the map object name as it appears in the contents. It will also return the base map type being used in the mapframe.
    print(eachMap.mapType) #return a string of the map type
                            #if the map is 2D, MAP is returned. If map is 3D, SCENE is returned.

#access the first map frame in the aprx (using the index in square brackets)
m = aprx_copy.listMaps("Map")[0]

#generate layer files from all the features in the workspace
listFC = arcpy.ListFeatureClasses()
for fc in listFC:
    #first step is to create a temporary layer from the list
    layer = arcpy.MakeFeatureLayer_management(fc)
    #next, we will save the feature layer as Layer files to a folder
    lyrFiles = arcpy.SaveToLayerFile_management(layer, "C:\\GEOS456\\FinalProject\\temp\\" + fc + ".lyrx")
    #reference them and add them back to the map; we have to use the arcpy.mp.LayerFile() function to create another mp module to reference and use to add the layers to the map
    lyrFile = MAP.LayerFile(lyrFiles)
    #after all that, we can add the layers to the map
    m.addLayer(lyrFile)
    print(fc + "layer added.")


#start to manage the layout after adding the layers to the map frame (the [] forces an index in this function only)
lyt = aprx_copy.listLayouts()[0]

#list all the layout elements in the layout frame
print(f"Layout width: {lyt.pageWidth}, height: {lyt.pageHeight}")
elements = lyt.listElements()
legends = lyt.listElements("LEGEND_ELEMENT")
for elem in elements:
    print(elem.name)
    print(elem.type) #will tell you if it is a legend, text, ect.


#change the title of the map layout
    if elem.name == "Map Title":
        elem.text = "Bear Habitat, Kananaskis"

#manage the legend title
    for lyr in m.listLayers():
        print(f"{lyr.name} - Visible: {lyr.visible}")

    for leg in legends:
        print(f"Legend name: {leg.name}")

    if elem.name == "Legend":
        elem.title = "Kananaskis Elements"

        leg_cim = elem.getDefinition('V2')
        leg_cim.titleSymbol.symbol.height = 30
        leg_cim.titleSymbol.symbol.horizontalAlignment = 'Center'
        leg_cim.titleSymbol.symbol.fontStyleName = 'Bold'
        leg_cim.titleSymbol.symbol.symbol.symbolLayers[0].color.values = [255,0,0,100]
        for itm in reversed(leg_cim.items):       #Done in reversed order
            itm.patchWidth = 50
        elem.setDefinition(leg_cim)

#move legend to bottom-right
        layout_width = 11
        layout_height = 17
        legend_width = 3.5
        legend_height = 2.3
        margin = 3
        elem.elementPositionX = 0.8522
        elem.elementPositionY = 4.3543

#get the first map frame from the layout
map_frame = lyt.listElements("MAPFRAME_ELEMENT")[0]

#set a specific map scale (e.g., 1:50,000)
map_frame.camera.scale = 350000

#refresh the layout view (optional, for ArcGIS Pro GUI)
map_frame.camera.setExtent(map_frame.camera.getExtent())

#export the finished map layout to a PDF (don't forget PDF extension)
lyt.exportToPDF(r"C:\GEOS456\FinalProject\FinalProject_RRB.pdf")

aprx_copy.save()

del aprx
del aprx_copy

#length of optimal routes
total_length = 0
with arcpy.da.SearchCursor("paths", ["SHAPE@LENGTH"]) as cursor:
    for row in cursor:
        total_length += row[0]


print(f"\nTotal length of optimal routes: {total_length/1000:.2f} km")

print("Zonal statistics table created for average elevation.")

print("\nFinal Dataset Summary\n")
arcpy.env.workspace = r"C:\GEOS456\FinalProject\KananaskisWildlife.gdb"
arcpy.env.workspace = gdb_path
#feature classes final description
print("Feature Classes:")

for fc in arcpy.ListFeatureClasses() or []:
        desc = arcpy.Describe(fc)
        print(f"Name: {fc}")
        print(f"  Shape Type: {desc.shapeType}")
        print(f"  Spatial Ref Name: {desc.spatialReference.name}")
        print(f"  Spatial Ref Type: {desc.spatialReference.type}")

# Rasters final description
print("Raster Datasets:")
for raster in arcpy.ListRasters() or []:
        input_raster = os.path.join(gdb_path, raster)
        desc = arcpy.Describe(input_raster)
        print(f"Name: {raster}")
        print(f"  Raster Format: {desc.format}")
        print(f"  Data Type: {desc.datasetType}")
        print(f"  Pixel Type: {desc.pixelType}")
        print(f"  Spatial Ref Name: {desc.spatialReference.name}")
        print(f"  Spatial Ref Type: {desc.spatialReference.type}")
        print(f"  Cell Size (X, Y): ({desc.meanCellWidth}, {desc.meanCellHeight})")


# Tables description
print("\nTables:")
for table in arcpy.ListTables() or []:
    print(f"Name: {table}")

print("\nAll dataset names finalized and summary complete. Ready for submission.")


#check in spatial extension when finished
arcpy.CheckInExtension("Spatial")
print("Spatial Extension Disengaged!")



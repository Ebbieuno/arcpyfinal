# **Final Project: Automating Map Creation Using ArcPy**

## **Overview**
This project demonstrates the use of Esri's **ArcPy** library to automate geospatial data processing and map creation. The script processes multiple datasets, performs raster and vector analyses, generates statistical summaries, and produces a high-quality PDF map. It was developed as the final project for a GIS programming course.

---

## **Features**
- Automates the creation of a geodatabase (GDB) for organizing geospatial data.
- Processes geospatial datasets (raster and vector) for a study area.
- Conducts spatial operations, including:
  - Projection and reprojection of datasets.
  - Clipping datasets to a specific boundary.
  - Raster reclassification and rescaling.
  - Weighted sum analysis for habitat suitability modeling.
- Generates statistical summaries such as elevation statistics and land cover areas.
- Produces a visual map layout exported as a PDF.
- Cleans up intermediate files and organizes outputs.

---

## **Requirements**
- **Software**: 
  - Esri ArcGIS Pro (or higher) with a valid license for the Spatial Analyst extension.
- **Python Environment**:
  - Python version compatible with ArcGIS Pro.
  - ArcPy library.
- **Input Data**:
  - A set of geospatial datasets (e.g., DEM, land cover, wildlife data) stored in specific folders.

---

## **Installation**
1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/Ebbieuno/arcpyfinal.git
   cd arcpyfinal

   Output:

All processed datasets are saved in KananaskisWildlife.gdb.
A PDF map is generated: FinalProject_RRB.pdf.
Customization
Study Area: Modify the input boundary shapefile (KCountry_Bound.shp) to analyze a different region.
Raster Weights: Adjust the weights in the WeightedSum tool to prioritize specific factors for habitat analysis.
Map Layout: Customize the map title, legend, and layout in the ArcGIS Pro project (GEOS456_FinalProject.aprx).
License
This project is licensed under The Unlicense, which dedicates your work to the public domain.

Acknowledgments
This project was developed for a GIS programming course at GEOS456.
Special thanks to Esri for providing the ArcPy library and tools.
   

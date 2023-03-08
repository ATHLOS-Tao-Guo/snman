# SNMan

**SNMan** is an under-development Python toolkit that lets you analyze street networks and model radical urban mobility transitions. It lets you export the updated street networks in OSM format that can be used in a transport modelling tool of your choice (e.g., MATSim, SUMO, etc.).

A detailed description is underway in an upcoming research paper:

  * Ballo, L. 2023. "SNMan: Modeling radical urban mobility transitions"
    *23rd Swiss Transport Research Conference*, Ascona, May 2023

SNMnan is being developed as part of the [E-Bike City](https://ebikecity.baug.ethz.ch/en/) project of
ETH Zurich, Department of Civil and Environmental Engineering.


## Getting Started

  * Install Python 3.9
  * Make sure you have installed the following dependencies: geopandas, osmnx, shapely, statistics, itertools, gdal, rasterio
  * Pull the *main* branch of this repository
  * [Download](https://polybox.ethz.ch/index.php/s/2yjdcNX1kJmgw8W) the *data_directory* starter kit
  and save it on your local machine
  * Start with *prepare_simplified_street_graph.ipynb* and *rebuild_street_graph.ipynb* for a complete process
    of network simplification and rebuilding into a system of one-way streets
  * Change the *data_directory* variable in both files to match the path of your *data_directory*
  * Use open *ebc_preview.qgz* in [QGIS](https://qgis.org/) to view the resulting datasets on a map


## Features

OSMnx is built on top of [OSMNx](https://osmnx.readthedocs.io/en/stable/), [GeoPandas](https://geopandas.org/), [NetworkX](https://networkx.org/), and [matplotlib](https://matplotlib.org/) and interacts with [OpenStreetMap](https://www.openstreetmap.org/) APIs to:

  * Download street networks
  * Simplify street graphs to obtain exactly one edge per street and one node per intersection (using a process that
    was further developed from OSMNx)
  * Match traffic volumes onto the network
  * Reallocate street space using customizable heuristics
  * Automatically arrange a system one-way streets
  * Export as GeoPackage and OSM

Planned:

  * Export as [GMNS](https://github.com/zephyr-data-specs/GMNS) format
  * Accessibility analyses and data export for time cartograms


## Contact

For questions or contributions, please contact
[Lukas Ballo](https://www.ivt.ethz.ch/personen/profil.lukas-ballo.html).


## License

SNMan is licensed under the MIT license. OpenStreetMap's open data [license](https://www.openstreetmap.org/copyright/)
requires that derivative works provide proper attribution.


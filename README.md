# ecog_data_analysis_notebooks

Notebooks for use in analysis pipeline for ToM Localizer and ToM and Attention (aka 2010) Task (Faces, Bio Motion and Movie to be added as analysis is finished, though many of the notebooks will crossover easily with some modifications). Includes *analysis.json documents for use with ecogtools.

### These notebooks should be run in the same directory that contains patient folders.
#### Example: 
- ecog_data_analysis *(folder)*
    - All analysis json files with parameters (one per patient and one per task)
    - example_notebook *(jupter notebook)*
    - patient_2002 *(folder)*
        - edf file *(edf)*
        - merged trigger *(csv)*
        - behavioral_data_2002 *(folder)*
            - ToM_Loc_2002.json
 
#### Image files created (from some notebooks) will be saved in new folder in patient folder (ex. patient_2002/ToM_Loc_plots/)

*All files/directories that begin with "patient" will be ignored within Github*

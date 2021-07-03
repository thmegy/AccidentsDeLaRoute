import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np



def getInputs(annee, communes):
    '''
    Get inputs for each selected year then apply mask to restrict to selected municipalities.
    Keep vehicule and user information only for remaining accidents. 
    '''
    if annee == '2019':
        sep = ';'
        dep = communes[0][:2]
    else:
        sep = ','
        dep = communes[0][:2] + '0'
        communes = [int(c[2:]) for c in communes]
        
    carac = pd.read_csv(f'input/{annee}/caracteristiques-{annee}.csv', sep=sep, dtype={'dep':str})
    lieu = pd.read_csv(f'input/{annee}/lieux-{annee}.csv', sep=sep)
    vehic = pd.read_csv(f'input/{annee}/vehicules-{annee}.csv', sep=sep)
    usager = pd.read_csv(f'input/{annee}/usagers-{annee}.csv', sep=sep)

    # combine caracteristics and location inputs
    df_comb = pd.merge(carac, lieu, on='Num_Acc')
    mask = np.logical_and( df_comb['com'].isin(communes), df_comb.dep == dep )
    df_sel = df_comb[mask]

    if df_sel.lat.dtype == 'O':
        # convert latitude and longitude to float
        lat = df_sel['lat'].str.slice_replace(start=2, stop=3, repl='.').astype(float)
        long = df_sel['long'].str.slice_replace(start=1, stop=2, repl='.').astype(float)
    else:
        lat = df_sel.lat / 100000
        long = df_sel.long / 100000
    df_sel = df_sel.drop(columns=['lat', 'long'])
    df_sel['lat'] = lat
    df_sel['long'] = long
    
    # remove NaN and 0
    df_sel = df_sel[np.logical_not( np.isnan(df_sel.long) )]
    df_sel = df_sel[ df_sel.long != 0. ]

    # restrict vehicle and user information to selected accidents
    acc_sel = df_sel.Num_Acc.to_numpy() # selected accidents
    vehic_sel = vehic[vehic.Num_Acc.isin(acc_sel)]
    usager_sel = usager[usager.Num_Acc.isin(acc_sel)] 
    
    return df_sel, vehic_sel, usager_sel





def drawMap(df_list, vehic_list, usager_list, annee, frontiere, route, vehic_type=None, usager_type=None):  
    '''
    Draw municipalities boundaries, the main roads within these boundaries and the corresponding accidents for each selected year.
    Accidents can be restricted to a given vehicle or user type.
    '''
    ax = frontiere.plot(color='white', edgecolor='black', linewidth=3)
    
    for i, df in enumerate(df_list):
        if vehic_type is not None:
            # accidents for a given type of vehicle
            acc_vehic = vehic_list[i][vehic_list[i].catv==vehic_type].Num_Acc.to_numpy()
            df_new = df[df.Num_Acc.isin(acc_vehic)]
            gdf = gpd.GeoDataFrame(df_new, geometry=gpd.points_from_xy(df_new.long, df_new.lat))
            gdf.plot(ax=ax, label=annee[i], alpha=0.7, markersize=100, color='red')
        elif usager_type is not None:
            # accidents for a given type of user
            mask_usa = usager_list[i].catu==usager_type
            mask_loc = np.logical_or( usager_list[i].locp == 3, usager_list[i].locp == 4 )
            acc_usa_pp = usager_list[i][np.logical_and(mask_usa, mask_loc)].Num_Acc.to_numpy()
            acc_usa_npp = usager_list[i][np.logical_and(mask_usa, np.logical_not(mask_loc))].Num_Acc.to_numpy()
            df_pp = df[df.Num_Acc.isin(acc_usa_pp)]
            df_npp = df[df.Num_Acc.isin(acc_usa_npp)]
            gdf_pp = gpd.GeoDataFrame(df_pp, geometry=gpd.points_from_xy(df_pp.long, df_pp.lat))            
            gdf_npp = gpd.GeoDataFrame(df_npp,
                                       geometry=gpd.points_from_xy(df_npp.long, df_npp.lat))            
            gdf_pp.plot(ax=ax, label='Sur passage piéton - {}'.format(annee[i]),
                        alpha=1, markersize=100, color='red')
            gdf_npp.plot(ax=ax, label='Hors passage piéton - {}'.format(annee[i]),
                         alpha=1, markersize=100, color='orange')
        else:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.long, df.lat))
            gdf.plot(ax=ax, label=annee[i], alpha=0.7, markersize=100, color='red')
        
    # Draw roads and streets
    route[route.fclass == 'primary'].plot(ax=ax, linewidth=3, color='grey')
    route[route.fclass == 'motorway'].plot(ax=ax, linewidth=3, color='grey')
    route[route.fclass == 'secondary'].plot(ax=ax, linewidth=2, color='grey')
    route[route.fclass == 'residential'].plot(ax=ax, linewidth=1, color='grey')
    route[route.fclass == 'unclassified'].plot(ax=ax, linewidth=1, color='grey')
    
    ax.legend()

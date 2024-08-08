import logging
import sys
import os

sys.path.append("/home/jupyter/news/src")
from utils import create_logger
logger = create_logger(__name__, "clustering.log")

import numpy as np
import pandas as pd

from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances, silhouette_score, calinski_harabasz_score
from tqdm import tqdm
import math

class Clustering:
    """
    A class used to perform hierarchical clustering and calculate various clustering metrics.

    Attributes
    ----------
    VALID_METRICS (list) : A list of valid metrics for clustering.
    VALID_LINKAGES (list) : A list of valid linkage methods for clustering.
    __percentile (float) : The percentile to use for determining the distance threshold.
    __linkage : (str) : The linkage method to use for clustering.
    __metric (str) : The distance metric to use for clustering.
    __model (AgglomerativeClustering) : The agglomerative clustering model.
    sil_scores (list) : A list to store silhouette scores for various distance thresholds.
    cal_scores (list) :A list to store Calinski-Harabasz scores for various distance thresholds.
    dist (list) : A list to store distance thresholds.
    clusters (list) : A list to store the number of clusters for various distance thresholds.
    index (int) : The index of the selected distance threshold based on the percentile.
    is_fitted (bool) : A flag indicating if the model has been fitted.
    ypred : (np.ndarray) : The predicted cluster labels.

    Methods
    -------
    __init__(percentile: float = 10, linkage: str = 'ward', metric: str = 'euclidean')
        Initializes the Clustering class.
    fit(xtrain: np.ndarray, n: int)
        Fits the clustering model and calculates silhouette scores for various distance thresholds.
    __generate_dynamic_range(xtrain: np.ndarray, n: int) -> list
        Generates a dynamic range of distance thresholds based on the pairwise distances of the data.
    distance_threshold() -> None
        Determines the distance threshold based on the percentile.
    display(x: list, y: list, ax, label: str, xlabel: str, ylabel: str, title: str = None)
        Displays a plot of the specified data.
    predict(xtrain: np.ndarray) -> np.ndarray
        Predicts clusters for the given data using the fitted model.
    """
    VALID_METRICS = ['euclidean', 'cosine', 'l1', 'l2', 'manhattan']
    VALID_LINKAGES = ['single', 'complete', 'average', 'ward']
    
    def __init__(self, percentile: float = 10, linkage = 'ward', metric = 'euclidean'):
        """
        Initializes the Clustering class.

        Args:
            percentile (float): The percentile to use for determining the distance threshold. Defaults to 10.
            linkage (str): The linkage method to use for clustering. Defaults to 'ward'.
            metric (str): The distance metric to use for clustering. Defaults to 'euclidean'.
        """
        self.__percentile = percentile
        self.__linkage = linkage
        self.__metric = metric
        self.__model = AgglomerativeClustering(distance_threshold=0.0, n_clusters=None, metric=self.__metric, linkage= self.__linkage)
        
        self.sil_scores :list[float] = []
        self.cal_scores :list[float] = []
        self.dist : list[float] = []
        self.clusters : list[float] = []
        self.index = None
        self.is_fitted = False
        self.ypred = None
    
    

    def fit(self, xtrain: np.ndarray, n: int):
        """
        Fits the clustering model and calculates silhouette scores for various distance thresholds.

        Args:
            xtrain (np.ndarray): The training data.
            n (int): The number of distance thresholds to evaluate.
        """
        range_values,  pairwise_distance = self.__generate_dynamic_range(xtrain, n=n)
        self.sil_scores, self.cal_scores, self.clusters, self.dist = [], [], [], []
        self.is_fitted  = False
        for distance_threshold in tqdm(range_values):
            try:
                self.__model.distance_threshold = distance_threshold
                ypred = self.__model.fit_predict(xtrain)
                sil_score = silhouette_score(pairwise_distance, ypred, metric='precomputed')
                self.sil_scores.append(sil_score)
                self.cal_scores.append(calinski_harabasz_score(xtrain, ypred))
                self.clusters.append(len(np.unique(ypred)))
                self.dist.append(distance_threshold)

            except ValueError as ve:
                logger.error(f"Exception at distance threshold {distance_threshold}. The distance threshold is too low, then the number of clusters is equal to to the number of sample while silhouette_score expect to have less number of clusters than the sample number.")
                

        self.is_fitted = True
        logger.info("Fitting complete.")

    def __generate_dynamic_range(self, xtrain: np.ndarray, n :int) -> list:
        """
        Generates a dynamic range of distance thresholds based on the pairwise distances of the data.

        Args:
            xtrain (np.ndarray): The training data.
            n (int): The number of distance thresholds to generate.

        Returns:
            list: A list of distance thresholds and the pairwise distance matrix.
        """
        pairwise_dist = pairwise_distances(xtrain, metric=self.__metric)
        min_dist = np.min(pairwise_dist)
        max_dist = np.max(pairwise_dist)
        step_size = (max_dist - min_dist) / n
        return [min_dist + i * step_size for i in range(1, n+1)], pairwise_dist

    def distance_threshold(self) -> None:
        """
        Determines the distance threshold based on the percentile.

        Raises:
            RuntimeError: If the model is not fitted yet.
        """
        if self.is_fitted:
            self.index = math.floor(len(self.dist) * (self.__percentile / 100))
        else:
            raise RuntimeError("Model is not fitted yet. Cannot determine distance threshold.")

    def predict(self, xtrain: np.ndarray) -> np.ndarray:
        """
        Predicts clusters for the given data using the fitted model.

        Args:
            xtrain (np.ndarray): The data to cluster.
            linkage (str): The linkage method to use for clustering. Defaults to 'ward'.

        Returns:
            np.ndarray: The predicted cluster labels.
        """
        if not self.is_fitted:
            logger.info("Model is not fitted yet. Fitting the model now.")
            self.fit(xtrain)
        self.distance_threshold()

        self.__model.distance_threshold = self.dist[self.index]
        self.ypred = self.__model.fit_predict(xtrain)
        return self.ypred
    
    
    # ---------------------------------- PROPERTIES -----------------------------------------------------------------------------------------------

    @property
    def metric(self) -> str:
        return self.__metric
    
    @metric.setter
    def metric(self, metric : str) -> None :
        
        if metric not in self.VALID_METRICS or not isinstance(metric, str) or metric is None:
            raise ValueError(f"Invlaid linkage = '{linkage}'. The valid ones are : {self.VALID_METRICS}")
        if self.__linkage == 'ward'  and metric != 'euclidean' :
            raise ValueError(f"Invalid metric = '{metric}'. The only valid matric for linkage = '{self.VALID_METRICS}' is 'euclidean' ")
        self.__metric = metric
        self.__model.metric = self.__metric
        
    @property
    def linkage(self) -> str:
        return self.__linkage
    
    @linkage.setter
    def linkage(self, linkage : str) -> None:
        if linkage not in self.VALID_LINKAGES or not isinstance(linkage, str) or linake is None:
            raise ValueError(f"Invlaid linkage = '{linkage}'. The valid ones are : {self.VALID_LINKAGES}")
        self.__linkage = linkage
        self.__model.linkage = self.__linkage
        
    @property
    def percentile(self) -> float:
        return self.__percentile
    
    @percentile.setter
    def percentile(self, percentile: float) -> None:
        self.__percentile = percentile
        self.distance_threshold()
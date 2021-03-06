from itertools import groupby
from math import *
from operator import itemgetter

from sklearn.cluster import dbscan

from BetterPlots import fancyPlot
from DistanceCalculator import *
from IO import *
from Smoothing import *

# Global stuff
almost_black = "#262626"


# http://stackoverflow.com/questions/1185408/converting-from-longitude-latitude-to-cartesian-coordinates
def clustering(lats, longs, timestamps, ID, timestmp, multiPDF=False):
    """
    Clusters the GPS coordinates using DBSCAN
    :param timestmp:                The timestamp
    :param ID:                      The ID
    :param timestamps:              The timestamps of the GPS coordinates
    :param lats:                    The latitudes
    :param longs:                   The longitudes
    :return:                        The rounded distance
    """
    folder = "out/"
    plotDir = folder + "plots/Walking Test Analysis"

    R = 6371  # Radius of the earth in km
    cartesianX = []
    cartesianY = []
    cartesianZ = []

    for lat, long in zip(lats, longs):
        # Convert to cartesian coordinates
        x = R * cos(lat) * cos(long)
        y = R * cos(lat) * sin(long)
        z = R * sin(lat)
        cartesianX.append(x)
        cartesianY.append(y)
        cartesianZ.append(z)

    combined = np.vstack((cartesianX, cartesianY, cartesianZ)).T
    (core_samples, labels) = dbscan(combined, eps=0.5)
    grouped = zip(labels, core_samples)
    nonGroupedPositions = []

    for (label, core_sample) in grouped:
        if label != -1:
            lat = lats[core_sample]
            long = longs[core_sample]
            stamp = timestamps[core_sample]
            nonGroupedPositions.append((lat, long, stamp))

    if len(nonGroupedPositions) > 0:
        y = zip(*nonGroupedPositions)[0]  # the latitudes
        x = zip(*nonGroupedPositions)[1]  # the longitudes
        t = zip(*nonGroupedPositions)[2]  # the timestamps
        x2, y2, newx2, newy2 = smooth(y, x, t)

        plt.plot(y2, x2, label="Linear Interpolation")
        plt.plot(newy2, newx2, label="Savgol Filter", color="r")
        distance = calcDistanceWalked(newy2, newx2)
        grouped = sorted(grouped, key=itemgetter(0))

        clusters = {}
        labels = []
        for key, group in groupby(grouped, key=itemgetter(0)):
            # group the clusters based on their label
            labels.append(key)
            clusters[key] = [el[1] for el in group]

        noise = False
        colors = plt.get_cmap("Spectral")(np.linspace(0, 1, len(clusters)))
        for label in labels:
            indices = clusters[label]
            latitudes = []
            longitudes = []
            size = 10
            alpha = 0.5
            lineWidth = 0.15
            for i in indices:
                latitudes.append(lats[i])
                longitudes.append(longs[i])
            if label == -1:
                # outliers are identified with a label of -1
                plt.plot(latitudes, longitudes, "o", markerfacecolor=almost_black, markeredgecolor=almost_black,
                         markersize=size, alpha=alpha, linewidth=lineWidth, label="Outlier")
                noise = True
            else:
                plt.plot(latitudes, longitudes, "o", markerfacecolor=colors[label], markeredgecolor=almost_black,
                         markersize=size, alpha=alpha, linewidth=lineWidth, label="Cluster %i" % (label + 1))

        plt.title("Timestamp: %s\n Number of clusters: %i\n Calculated distance: %i meters" % (
            timestmp, (len(clusters) - 1) if noise else len(clusters), round(distance)))
        plt.xlabel("Latitude")
        plt.ylabel("Longitude")
        fancyPlot()
        writeToPdf(ID, plotDir)
        return True, distance
    else:
        # DBSCAN gave back an empty array, therefore we cannot perform any smoothing or distance calculation
        return False, 0

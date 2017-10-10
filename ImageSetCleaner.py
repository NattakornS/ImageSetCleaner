import numpy as np
from PIL import Image
import os
from win32api import GetSystemMetrics
from Saliency import get_saliency_ft_direct,get_saliency_mbd
from sklearn.metrics import accuracy_score,precision_score,recall_score
from skimage.io import imread_collection
from sklearn import cluster
from sklearn import mixture
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn import svm
import cv2
import time
from sklearn import cluster, datasets


# Check :
# https://machinelearningmastery.com/how-to-identify-outliers-in-your-data/
# http://scikit-learn.org/stable/auto_examples/covariance/plot_outlier_detection.html#sphx-glr-auto-examples-covariance-plot-outlier-detection-py

# http://www.sciencedirect.com/science/article/pii/S0167947307002204
# https://www.researchgate.net/publication/224576812_Using_one-class_SVM_outliers_detection_for_verification_of_collaboratively_tagged_image_training_sets


# TODO : Get incepetion
# TODO : Simple visualiser ( Tkinter ?)
def load_image(path, width, length):
    path = os.path.abspath(path) + '\\'

    col = imread_collection(path + '*.jpg')
    col = np.array(col)

    # Check for alpha
    for idx, elem in enumerate(col):
        if not elem.shape[2] == 3:
            col[idx] = cv2.cvtColor(elem, cv2.COLOR_RGBA2RGB)

    col = np.array([cv2.resize(im, (width, length)) for im in col])

    return col


def load_saliency(path, width, length):
    collection = load_image(path, width, length)

    return np.array([get_saliency_ft_direct(img) for img in collection])


def stich_images(shape, images):
    width_screen = GetSystemMetrics(0)
    height_screen = GetSystemMetrics(1)

    nb_images = len(images)

    images_in_line_max = width_screen // shape[0]
    images_in_column_max = height_screen // shape[1]

    #images = [img.resize(shape, Image.ANTIALIAS) for img in images]

    stitched_image = Image.new('RGB', (width_screen, height_screen))

    for idx_line in range(images_in_line_max):
        for idx_column in range(images_in_column_max):

            if idx_line * images_in_column_max + idx_column >= nb_images:
                break
            img_with_pil = Image.fromarray(images[idx_line * images_in_column_max + idx_column])
            stitched_image.paste(im=img_with_pil, box=(idx_line * shape[0], idx_column * shape[1]))

    stitched_image.show()


def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])


"""
    N.B : The detector breaks with a full black image.
"""
def outlier_detection_check(image_set, ground_true):
    t0 = time.time()
    # Rgb2gray
    if len(image_set.shape) > 3:
        image_set = np.array([rgb2gray(im_rgb) for im_rgb in image_set])

    # Flatten image
    image_set = np.reshape(image_set, [image_set.shape[0], -1])


    # http://scikit-learn.org/stable/modules/generated/sklearn.cluster.bicluster.SpectralBiclustering.html
    # clf = cluster.SpectralBiclustering(n_clusters=2, method='log', random_state=42, svd_method="arpack")
    # clf.fit(image_set)
    #
    # predictions = clf.row_labels_

    # http://scikit-learn.org/stable/auto_examples/cluster/plot_agglomerative_clustering.html#sphx-glr-auto-examples-cluster-plot-agglomerative-clustering-py
    clf = cluster.AgglomerativeClustering(n_clusters=2)
    clf.fit(image_set)
    predictions = clf.labels_
    #print(predictions)
    sum_row_labels = np.sum(predictions)
    majority_class = np.sum(predictions) > (len(predictions) / 2 - 1)
    #print(predictions)
    #print(majority_class)
    print(predictions)
    if majority_class:
        ground_true = 1 - ground_true

    #print(ground_true)

    print('Accuracy :', str(accuracy_score(ground_true, predictions))[:4], 'Precision',
          str(precision_score(ground_true, predictions))[:6], 'Recall', str(recall_score(ground_true, predictions))[:6])

    print('Time taken for classification :', time.time() - t0)

    detected_images = [im.reshape([180, 280]) for idx, im in enumerate(image_set) if predictions[idx] == 1]
    # if len(detected_images) >25:
    sent_images = 0
    image_sent_one_go = 30
    while sent_images + image_sent_one_go < len(detected_images):
        stich_images((280, 180), detected_images[sent_images:sent_images+image_sent_one_go])
        sent_images += image_sent_one_go

    stich_images((280, 180), detected_images[sent_images:])


def main():

    width = 280
    length = 180

    dir_location = ['./Test_cluster_no_outlier/', './Test_cluster_small/', './Test_cluster_1/', './Test_cluster_2/']
    # 0 inlier, 1 outlier
    ground_true = [np.zeros(75), np.array([0, 0, 0, 0, 1, 1, 0, 1, 0, 0]), np.concatenate([[1, 1, 1, 1], np.zeros(52)]),
                   np.concatenate([np.zeros(82), [1, 1, 1, 1, 1]])]

    dir_location = dir_location[1:]
    ground_true = ground_true[1:]

    for idx, dir in enumerate(dir_location):
        print("Currenty at :", dir)
        image_set = load_image(dir, width, length)
        #stich_images((width, length), image_set)

        outlier_detection_check(image_set, ground_true[idx])

        t0 = time.time()
        image_set = load_saliency(dir, width, length)
        print('Time to get saliency :', time.time() - t0)

        #stich_images((width, length), image_set)

        outlier_detection_check(image_set, ground_true[idx])



    # clf = mixture.BayesianGaussianMixture(n_components=2)
    # clf.fit(image_set)
    # print(clf.predict(image_set))

    #
    # outliers_fraction = 0.25
    #
    # classifiers = {
    #     "One-Class SVM": svm.OneClassSVM(nu=0.95 * outliers_fraction + 0.05,
    #                                      kernel="rbf", gamma=0.1),
    #     "Robust covariance": EllipticEnvelope(contamination=outliers_fraction),
    #     "Isolation Forest": IsolationForest(max_samples=n_samples,
    #                                         contamination=outliers_fraction,
    #                                         random_state=rng),
    #     "Local Outlier Factor": LocalOutlierFactor(
    #         n_neighbors=35,
    #         contamination=outliers_fraction)}
    #
    # for i, (clf_name, clf) in enumerate(classifiers.items()):
    #     # fit the data and tag outliers
    #     if clf_name == "Local Outlier Factor":
    #         y_pred = clf.fit_predict(X)
    #         scores_pred = clf.negative_outlier_factor_
    #     else:
    #         clf.fit(X)
    #         scores_pred = clf.decision_function(X)
    #         y_pred = clf.predict(X)
    #     threshold = stats.scoreatpercentile(scores_pred,
    #                                         100 * outliers_fraction)
    #     n_errors = (y_pred != ground_truth).sum()
    #     # plot the levels lines and the points
    #     if clf_name == "Local Outlier Factor":
    #         # decision_function is private for LOF
    #         Z = clf._decision_function(np.c_[xx.ravel(), yy.ravel()])
    #     else:
    #         Z = clf.decision_function(np.c_[xx.ravel(), yy.ravel()])
    #     Z = Z.reshape(xx.shape)



if __name__ == '__main__':
    main()
import wfdb
import peakutils
from rpeakdetection.Utility import Utility
import numpy as np
from rpeakdetection.rpeak_detector import RPeakDetector
import matplotlib.pyplot as plt
from collections import defaultdict
from beatclassification.LabelsExtraction import LabelsExtraction
import time
import sys

PATH = 'data/ecg/mitdb/'
util = Utility()
rpeak = RPeakDetector()
eval_width = 36
class PeakDetector():

    def choose_tresholds(self, thresholds):
        precisions = defaultdict(list)
        recalls = defaultdict(list)
        for name in wfdb.get_record_list('mitdb'):
            print(name)
            for thresh in thresholds:
                record, indices = self.detect_peaks(name, thresh)
                recall, precision = rpeak.evaluate(indices, PATH + name, eval_width, rule_based=False)
                precisions[thresh].append(precision)
                recalls[thresh].append(recall)
        average_prec = [np.mean(precisions[t]) for t in thresholds]
        average_rec = [np.mean(recalls[t]) for t in thresholds]
        thresh_index = np.argmax([(average_prec[j] + average_rec[j])/2 for j in range(len(average_rec))])
        best_threshold = thresholds[thresh_index]
        plt.plot([best_threshold]*2, [0, 1], label='best_threshold')
        plt.plot(thresholds, average_prec, label = 'precision')
        plt.plot(thresholds, average_rec, label = 'recall')
        plt.xlabel('threshold')
        plt.ylabel('precision/recall')
        plt.legend()
        print(average_rec)
        print(average_prec)
        plt.savefig('prec-rec-threshold-generic.png')
        return best_threshold

    def detect_peaks(self, name, thresh):
        record = self.preprocess(name)
        return record, peakutils.indexes(record, thres=thresh, min_dist=40)

    def preprocess(self, name):
        record = wfdb.rdrecord(PATH + name, channels=[0])
        record = record.p_signal.flatten()
        record = np.abs(record)
        record = np.divide(record, np.max(record))
        return record

    def plot_criticism(self, signal, name, peaks,  threshold=None):
        real_peaks = util.remove_non_beat('data/ecg/mitdb/' + name, False)[0]
        # compute the first wrong detection
        critics = list(filter(lambda x :min(np.abs([x - real_peaks[q] for q in range(len(real_peaks))])) > 18, peaks))
        if len(critics) == 0:
            print("no crticisms")
            sys.exit()
        else:
            critic = critics[0]
            real_index = np.argmin(np.abs([critic - real_peaks[q] for q in range(len(real_peaks))]))
            real_plot = real_peaks[real_index]
            plot_from = max(0,min(real_plot, critic) -30)
            plot_to = max(real_plot, critic) + 30
            fig, ax = plt.subplots()
            signal_plot = signal[plot_from:plot_to]
            min_y = min(signal_plot)
            max_y = max(signal_plot)
            plt.plot([real_plot - 18, real_plot - 18], [min_y, max_y], '--', label='start evaluation window')
            plt.plot([real_plot + 18, real_plot + 18], [min_y, max_y], '--', label='end evaluation window')
            ax.scatter([real_plot], [signal[real_plot]], color ='blue', label = 'real_peaks')
            ax.scatter([critic], [signal[critic]], color ='red', label = 'detected_peak')
            plt.plot(np.arange(plot_from, plot_to), signal_plot)
            if threshold is not None:
                plt.plot([0, plot_to], [threshold]*2, label = 'threshold')
            ax.legend()
            plt.legend()
            plt.savefig("criticism.png")
            plt.close()
            return critic, real_plot

    def signals_evaluation(self, threshold):
        precisions = list()
        recalls = list()
        for name in wfdb.get_record_list('mitdb'):
            start_time = time.time()
            record, indices = self.detect_peaks(name, threshold)
            elapsed = time.time() - start_time
            print(elapsed/len(record))
            precision, recall = rpeak.evaluate(indices, PATH +name, eval_width, False)
            precisions.append(precision)
            recalls.append(recall)
            print('{:s}, {:f}, {:f}'.format(name, precision, recall))
        av = 'average'
        print("{:s}, {:f}, {:f}".format(av, np.mean(precisions), np.mean(recalls)))


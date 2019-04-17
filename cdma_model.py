from Ner import Ner
from src.model.data_utils import NERDataset
from src.model.sal_blstm_oal_crf_model import SAL_BLSTM_OAL_CRF_Model
from src.model.config import Config
from src.transfer2target import get_tensors_in_checkpoint_file, build_tensors_in_checkpoint_file
import os
import tensorflow as tf
from tensorflow.python import pywrap_tensorflow



class CDMAModel(Ner):

    def save_model(self, file):
        self.model.save_session()

    def load_model(self, file):
        self.model.build()
        CHECKPOINT_NAME = "src/source_model/model_weights"
        restored_vars = get_tensors_in_checkpoint_file(file_name=CHECKPOINT_NAME)
        tensors_to_load = build_tensors_in_checkpoint_file(restored_vars)
        self.model.saver = tf.train.Saver(tensors_to_load)
        self.model.restore_session("src/source_model/")
        self.model.reinitialize_weights("proj")

    def __init__(self, dataset_name):
        """
              initialize config
              build model
        """
        self.config = Config()
        self.config.filename_train = "datasets/"+dataset_name+"/train"
        self.config.filename_dev = "datasets/"+dataset_name+"/dev"
        self.config.filename_test = "datasets/"+dataset_name+"/test"

        self.config.filename_chars = self.config.filename_chars.replace("source", "target")
        self.config.filename_glove = self.config.filename_glove.replace("source", "target")
        self.config.filename_tags = self.config.filename_tags.replace("source", "target")
        self.config.filename_words = self.config.filename_words.replace("source", "target")

        self.config.dir_model = self.config.dir_model.replace("source", "target")
        self.config.dir_output = self.config.dir_output.replace("source", "target")
        self.config.path_log = self.config.path_log.replace("source", "target")

        os.environ["CUDA_VISIBLE_DEVICES"] = str(self.config.gpu_ids[0])
        self.model = SAL_BLSTM_OAL_CRF_Model(self.config)

    def convert_ground_truth(self, data, *args, **kwargs):
        """
        Not applicable to my implementation.
        :param data:
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def read_dataset(self, filedict, dataset_name,*args, **kwargs):
        """

        :param fileNames:
        :param args:
        :param kwargs:
        :return: dataset
        create instance of  NERDataset for  creating dataset
        """
        self.train_data = NERDataset(self.config.filename_train, self.config.processing_word,
                           self.config.processing_tag, self.config.max_iter)

        self.dev_data = NERDataset(self.config.filename_dev, self.config.processing_word,
                         self.config.processing_tag, self.config.max_iter)
        self.test_data = NERDataset(self.config.filename_test, self.config.processing_word,
                          self.config.processing_tag, self.config.max_iter)

    def train(self, data, *args, **kwargs):
        """
        :param data: train dataset
        :param args: dev dataset
        :param kwargs: Null
        :return:
        call model.train(data,  dev)
        """
        self.model.train(self.train_data, self.dev_data)

    def predict(self, data, *args, **kwargs):
        """

        :param data: test
        :param args:
        :param kwargs:
        :return: preds, lentgth
        call model.predict_batch(data)
        """
        return self.model.predict(data)

    def evaluate(self, predictions, groundTruths, *args, **kwargs):
        """

        :param predictions:  test data withr tags
        :param groundTruths:  Null
        :param args:  Null
        :param kwargs:  Null
        :return:  f1, recall, precision
        call model.evaluation(test)

        """
        self.model.evaluate(self.test_data)




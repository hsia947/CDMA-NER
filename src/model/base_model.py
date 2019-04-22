import os
import tensorflow as tf


class BaseModel(object):
    """Generic class for general methods that are not specific to NER"""

    def __init__(self, config):
        """Defines self.config and self.logger

        Args:
            config: (Config instance) class with hyper parameters,
                vocab and embeddings

        """
        self.config = config
        self.logger = config.logger
        self.sess   = None
        self.saver  = None


    def reinitialize_weights(self, scope_name):
        """Reinitializes the weights of a given layer"""
        variables = tf.contrib.framework.get_variables(scope_name)
        init = tf.variables_initializer(variables)
        self.sess.run(init)


    def add_train_op(self, lr_method, lr, loss, clip=-1, psi=None):
        """Defines self.train_op that performs an update on a batch

        Args:
            lr_method: (string) sgd method, for example "adam"
            lr: (tf.placeholder) tf.float32, learning rate
            loss: (tensor) tf.float32 loss to minimize
            clip: (python float) clipping of gradient. If < 0, no clipping

        """
        _lr_m = lr_method.lower() # lower to make sure
        psi = self.config.psi
        with tf.variable_scope("train_step"):
            if _lr_m == 'adam': # sgd method
                optimizer_base = tf.train.AdamOptimizer(lr)
                optimizer_adapt = tf.train.AdamOptimizer(lr * psi)
            elif _lr_m == 'adagrad':
                optimizer_base = tf.train.AdagradOptimizer(lr)
                optimizer_adapt = tf.train.AdagradOptimizer(lr * psi)
            elif _lr_m == 'sgd':
                optimizer_base = tf.train.GradientDescentOptimizer(lr)
                optimizer_adapt = tf.train.GradientDescentOptimizer(lr * psi)
            elif _lr_m == 'rmsprop':
                optimizer_base = tf.train.RMSPropOptimizer(lr)
                optimizer_adapt = tf.train.RMSPropOptimizer(lr * psi)
            else:
                raise NotImplementedError("Unknown method {}".format(_lr_m))

            var_base = []
            var_adaption = []
            for v in tf.global_variables():
                print(v.name)
                if 'adapt' in v.name or 'transition' in v.name or 'proj/' in v.name:
                    var_adaption.append(v)
                else:
                    var_base.append(v)

            if clip > 0: # gradient clipping if clip is positive
                grads_adapt, vs_adapt     = zip(*optimizer_adapt.compute_gradients(loss, var_list=var_adaption))
                grads_adapt, gnorm_adapt  = tf.clip_by_global_norm(grads_adapt, clip)
                train_op_adaption = optimizer_adapt.apply_gradients(zip(grads_adapt, vs_adapt))

                grads_base, vs_base = zip(*optimizer_base.compute_gradients(loss, var_list=var_base))
                grads_base, gnorm_base = tf.clip_by_global_norm(grads_base, clip)
                train_op_base = optimizer_base.apply_gradients(zip(grads_base, vs_base))

            else:
                train_op_adaption = optimizer_adapt.minimize(loss, var_list=var_adaption)
                train_op_base = optimizer_base.minimize(loss, var_list=var_base)

            self.train_op = tf.group(train_op_adaption, train_op_base)


    def initialize_session(self):
        """Defines self.sess and initialize the variables"""
        self.logger.info("Initializing tf session")
        self.sess = tf.Session()
        self.sess.run(tf.global_variables_initializer())
        self.saver = tf.train.Saver()


    def restore_session(self, dir_model):
        """Reload weights into session

        Args:
            sess: tf.Session()
            dir_model: dir with weights

        """
        self.logger.info("Reloading the latest trained model...")
        self.saver.restore(self.sess, tf.train.latest_checkpoint(dir_model))


    def save_session(self):
        """Saves session = weights"""
        if not os.path.exists(self.config.dir_model):
            os.makedirs(self.config.dir_model)
        self.saver.save(self.sess, self.config.dir_model)
        print("Save session succeed")


    def close_session(self):
        """Closes the session"""
        self.sess.close()


    def add_summary(self):
        """Defines variables for Tensorboard

        Args:
            dir_output: (string) where the results are written

        """
        self.merged      = tf.summary.merge_all()
        self.file_writer = tf.summary.FileWriter(self.config.dir_output,
                self.sess.graph)


    def train(self, train, dev):
        """Performs training with early stopping and lr exponential decay

        Args:
            train: dataset that yields tuple of (sentences, tags)
            dev: dataset

        """
        best_score = 0
        nepoch_no_imprv = 0 # for early stopping
        self.add_summary() # tensorboard
        lost_list = []
        acc_list = []
        for epoch in range(self.config.nepochs):
            self.logger.info("Epoch {:} out of {:}".format(epoch + 1,
                        self.config.nepochs))

            score, loss_hist, train_acc_hist = self.run_epoch(train, dev, epoch)
            self.config.lr *= self.config.lr_decay # decay learning rate

            # early stopping and saving best parameters
            if score >= best_score:
                nepoch_no_imprv = 0
                self.save_session()
                best_score = score
                self.logger.info("- new best score!")
                lost_list.extend(loss_hist)
                acc_list.append(train_acc_hist)
            else:
                nepoch_no_imprv += 1
                if nepoch_no_imprv >= self.config.nepoch_no_imprv:
                    self.logger.info("- early stopping {} epochs without "\
                            "improvement".format(nepoch_no_imprv))

                    break
        return lost_list, acc_list


    def evaluate(self, test):
        """Evaluate model on test set

        Args:
            test: instance of class Dataset

        """
        self.logger.info("Testing model over test set")
        metrics = self.run_evaluate(test)
        msg = " - ".join(["{} {:04.2f}".format(k, v)
                for k, v in metrics.items()])
        self.logger.info(msg)
        return metrics

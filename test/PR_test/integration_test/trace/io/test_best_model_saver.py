import os
import tempfile
import unittest

import tensorflow as tf
import torch

import fastestimator as fe
from fastestimator.op.tensorop.model import UpdateOp
from fastestimator.test.unittest_util import MultiLayerTorchModel, is_equal, one_layer_tf_model
from fastestimator.trace.io import BestModelSaver
from fastestimator.util.data import Data


def one_layer_model_without_weights():
    input = tf.keras.layers.Input([3])
    x = tf.keras.layers.Dense(units=1, use_bias=False)(input)
    model = tf.keras.models.Model(inputs=input, outputs=x)
    return model


class MultiLayerTorchModelWithoutWeights(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc1 = torch.nn.Linear(4, 2, bias=False)
        self.fc2 = torch.nn.Linear(2, 1, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.fc2(x)
        return x


class TestBestModelSaver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.save_dir = tempfile.gettempdir()
        cls.tf_model = fe.build(model_fn=one_layer_tf_model, optimizer_fn='adam', model_name='tf')
        cls.torch_model = fe.build(model_fn=MultiLayerTorchModel, optimizer_fn='adam', model_name='torch')
        cls.data = Data({'loss': 0.5})
        cls.state = {'mode': 'train', 'epoch': 1, 'warmup': False}
        cls.tf_input_data = tf.Variable([[2.0, 1.5, 1.0], [1.0, -1.0, -0.5]])
        cls.tf_y = tf.constant([[-6], [1]])
        cls.torch_input_data = torch.tensor([[1.0, 1.0, 1.0, -0.5], [0.5, 1.0, -1.0, -0.5]], dtype=torch.float32)
        cls.torch_y = torch.tensor([[5], [7]], dtype=torch.float32)

    def test_tf_model(self):
        op = UpdateOp(model=self.tf_model, loss_name='loss')
        with tf.GradientTape(persistent=True) as tape:
            self.state['tape'] = tape
            pred = fe.backend.feed_forward(self.tf_model, self.tf_input_data)
            loss = fe.backend.mean_squared_error(y_pred=pred, y_true=self.tf_y)
            output = op.forward(data=loss, state=self.state)
        bms = BestModelSaver(model=self.tf_model, save_dir=self.save_dir)
        bms.on_epoch_end(data=self.data)
        m2 = fe.build(model_fn=one_layer_model_without_weights, optimizer_fn='adam')
        fe.backend.load_model(m2, os.path.join(self.save_dir, 'tf_best_loss.h5'))
        self.assertTrue(is_equal(m2.trainable_variables, self.tf_model.trainable_variables))

    def test_torch_model(self):
        op = UpdateOp(model=self.torch_model, loss_name='loss')
        pred = fe.backend.feed_forward(self.torch_model, self.torch_input_data)
        loss = fe.backend.mean_squared_error(y_pred=pred, y_true=self.torch_y)
        output = op.forward(data=loss, state=self.state)
        bms = BestModelSaver(model=self.torch_model, save_dir=self.save_dir)
        bms.on_epoch_end(data=self.data)
        m2 = fe.build(model_fn=MultiLayerTorchModelWithoutWeights, optimizer_fn='adam')
        fe.backend.load_model(m2, os.path.join(self.save_dir,'torch_best_loss.pt'))
        self.assertTrue(is_equal(list(m2.parameters()), list(self.torch_model.parameters())))

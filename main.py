from cdma_model import CDMAModel


def main(input_file_path):

    model = CDMAModel(input_file_path)
    model.load_model("target_model/model_weights", "target_model/") #pretrained model
    model.read_dataset(None, None)
    model.train(None)
    p, f1, r = model.evaluate(None, None)
    output_path = model.predict(input_file_path+"/test")
    return output_path


if __name__ == "__main__":
    path = "datasets/ritter2011"
    out_path = main(path)
    print("Predict_output_path: ", out_path)

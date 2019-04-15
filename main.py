from cdma_model import CDMAModel


def main():
    model = CDMAModel()
    model.load_model(None)
    model.read_dataset(None, None)
    model.train(None)
    model.evaluate(None, None)

if __name__ == "__main__":
    main()

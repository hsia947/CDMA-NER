from cdma_model import CDMAModel


def main():
    model = CDMAModel()
    model.build()
    model.read_dataset(None, None)
    model.train(None)
    model.evaluate(None, None)

if __name__ == "__main__":
    main()

import av_social_trust as av


car = av.Car()
car.add_driver(
    agent_id=0,
    self_trust=0.9,
    opinion=0.5,
    attention=1,
    self_trust_learning_rate=0.1,
)


if __name__ == "__main__":
    print(car)
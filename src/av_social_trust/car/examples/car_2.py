import av_social_trust as av


car = av.Car()
driver_id = 0
passenger_id = 1
car.add_driver(
    agent_id=driver_id,
    self_trust=0.9,
    opinion=0.5,
    attention=1,
    self_trust_learning_rate=0.1,
)
car.add_passenger(
    agent_id=passenger_id,
    self_trust=0.8,
    opinion=0.6,
    attention=0.5,
    self_trust_learning_rate=0.2
)
car.connect_agents(
    agent_from_id=driver_id,
    agent_to_id=passenger_id,
    trust=0.7,
    trust_learning_rate=0.3,
    homophilic_normative_tradeoff=0.5
)


if __name__ == "__main__":
    print(car)
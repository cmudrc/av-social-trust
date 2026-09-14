import av_social_trust as av
from av_social_trust.cognitive.state.examples import (
    cognitive_state_1,
    cognitive_state_2,
    cognitive_state_3,
)


car = av.Car()
driver_id = 0
passenger_1_id = 1
passenger_2_id = 2

car.add_driver(
    agent_id=driver_id,
    self_trust=0.9,
    cognitive_state=cognitive_state_1,
    self_trust_learning_rate=0.1,
)
car.add_passenger(
    agent_id=passenger_1_id,
    self_trust=0.8,
    cognitive_state=cognitive_state_2,
    self_trust_learning_rate=0.2
)
car.add_passenger(
    agent_id=passenger_2_id,
    self_trust=0.7,
    cognitive_state=cognitive_state_3,
    self_trust_learning_rate=0.15
)

car.connect_agents(
    agent_from_id=driver_id,
    agent_to_id=passenger_1_id,
    trust=0.7,
    trust_learning_rate=0.3,
    homophilic_normative_tradeoff=0.5
)
car.connect_agents(
    agent_from_id=passenger_1_id,
    agent_to_id=driver_id,
    trust=0.5,
    trust_learning_rate=0.3,
    homophilic_normative_tradeoff=0.5
)
car.connect_agents(
    agent_from_id=driver_id,
    agent_to_id=passenger_2_id,
    trust=0.7,
    trust_learning_rate=0.3,
    homophilic_normative_tradeoff=0.5
)
car.connect_agents(
    agent_from_id=passenger_2_id,
    agent_to_id=driver_id,
    trust=0.5,
    trust_learning_rate=0.3,
    homophilic_normative_tradeoff=0.5
)
car.connect_agents(
    agent_from_id=passenger_1_id,
    agent_to_id=passenger_2_id,
    trust=0.3,
    trust_learning_rate=0.2,
    homophilic_normative_tradeoff=0.5
)


if __name__ == "__main__":
    print(car)

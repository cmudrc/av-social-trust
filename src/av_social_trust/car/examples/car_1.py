import av_social_trust as av
from av_social_trust.cognitive.state.examples import cognitive_state_1


car = av.Car()
car.add_driver(
    agent_id=0,
    self_trust=0.9,
    cognitive_state=cognitive_state_1,
    self_trust_learning_rate=0.1,
)


if __name__ == "__main__":
    print(car)

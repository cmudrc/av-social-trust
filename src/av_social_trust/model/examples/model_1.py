import av_social_trust as av

from av_social_trust.car.examples import car_1 as car
from av_social_trust.generator import generate_situations


model = av.Model(
    car=car,
)


if __name__ == "__main__":
    for situation in generate_situations(6, block_size=2, unavailable_steps=1):
        state = model.step(situation)
        print(
            f"Cycle {model.cycle}: complexity={situation.task_complexity}, "
            f"available={situation.automation_available}, "
            f"driver opinion={state['opinion_vector'][0]:.2f}, "
            f"automation on={state['automation_on']}"
        )

import av_social_trust as av

from av_social_trust.car.examples import car_1 as car
from av_social_trust.situation.generator.examples import situation_generator_1 as situation_generator


model = av.Model(
    car=car,
)


if __name__ == "__main__":
    situations = situation_generator.generate_series(6)
    for situation in situations:
        state = model.step(situation)
        print(
            f"Cycle {model.cycle}: complexity={situation.task_complexity}, "
            f"available={situation.automation_available}, "
            f"driver opinion={state['opinion_vector'][0]:.2f}, "
            f"automation on={state['automation_on']}"
        )

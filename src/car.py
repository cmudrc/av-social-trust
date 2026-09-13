from copy import deepcopy
import networkx as nx


def validate_range(
    value: float,
    name: str,
    min: float,
    max: float
):
    if value < min or value > max:
        raise ValueError(f"{name} has value of {str(value)} but \
                         must be between {str(min)} and {str(max)}")


class Car:

    def __init__(self):
        self.G = nx.DiGraph()
        self._has_driver = False

    def _add_agent(
        self,
        agent_id: int,
        role: str,
        attention: float,
        self_trust: float,
        opinion: float,
        self_trust_learning_rate: float
    ):
        if self._has_node(agent_id):
            raise ValueError(f"Agent {agent_id} already exists.")
        
        validate_range(attention, "attention", 0.0, 1.0)
        validate_range(self_trust, "self_trust", 0.0, 1.0)
        validate_range(opinion, "initial_opinion", -1.0, 1.0)
        validate_range(self_trust_learning_rate, "self_trust_learning_rate", 0.0, 1.0)

        self.G.add_node(
            agent_id,
            role=role,
            attention=attention,
            self_trust=self_trust,
            opinion=opinion,
            self_trust_learning_rate=self_trust_learning_rate,
        )

    def _has_node(self, node_id: int) -> bool:
        return node_id in self.G.nodes

    def _has_edge(self, node_1_id: int, node_2_id: int) -> bool:
        return self.G.has_edge(node_1_id, node_2_id)

    def add_driver(
        self,
        agent_id: int,
        self_trust: float,
        opinion: float,
        attention: float,
        self_trust_learning_rate: float,
    ):
        if not self._has_driver:
            self._add_agent(
                agent_id=agent_id,
                role="driver",
                attention=attention,
                self_trust=self_trust,
                opinion=opinion,
                self_trust_learning_rate=self_trust_learning_rate
            )
        else:
            raise Exception("Driver already exists in the car.")

    def add_passenger(
        self,
        agent_id: int,
        self_trust: float,
        opinion: float,
        attention: float,
        self_trust_learning_rate: float
    ):
        self._add_agent(
            agent_id=agent_id,
            role="passenger",
            attention=attention,
            self_trust=self_trust,
            opinion=opinion,
            self_trust_learning_rate=self_trust_learning_rate
        )

    def connect_agents(
        self,
        agent_from_id: int,
        agent_to_id: int,
        trust: float,
        trust_learning_rate: float,
        homophilic_normative_tradeoff: float,
    ):
        if not self._has_node(agent_from_id) or not self._has_node(agent_to_id):
            raise ValueError(f"Agent {agent_from_id} or {agent_to_id} does not exist.")

        validate_range(trust, "trust", 0.0, 1.0)
        validate_range(trust_learning_rate, "trust_learning_rate", 0.0, 1.0)
        validate_range(homophilic_normative_tradeoff, "homophilic_normative_tradeoff", 0.0, 1.0)

        self.G.add_edge(
            agent_from_id,
            agent_to_id,
            trust=trust,
            trust_learning_rate=trust_learning_rate,
            homophilic_normative_tradeoff=homophilic_normative_tradeoff
        )

    @property
    def driver(self) -> int:
        for agent_id, data in self.G.nodes(data=True):
            if data["role"] == "driver":
                return agent_id
        raise ValueError("No driver exists in the car.")

    @property
    def passengers(self) -> list[int]:
        return [
            agent_id
            for agent_id, data in self.G.nodes(data=True)
            if data["role"] == "passenger"
        ]

    @property
    def agents(self) -> list[int]:
        driver = self.driver
        passengers = self.passengers
        agents = [driver, *passengers]
        return agents

    def to_state(self):
        """
        Export an independent snapshot in driver-first agent order.

        Entry [i][j] describes agent i's trust in agent j. Trust is raw,
        not row-normalized. Diagonal connections represent self-trust;
        their tradeoff entries are unused and remain zero. Social appraisal
        averages must exclude the diagonal and any masked-out connections.
        """
        driver = self.driver
        agents = self.agents
        opinion_vector = [self.G.nodes[agent]["opinion"] for agent in agents]
        attention_vector = [self.G.nodes[agent]["attention"] for agent in agents]
        size = len(agents)
        connection_mask_matrix = [[False] * size for _ in agents]
        trust_matrix = [[0.0] * size for _ in agents]
        learning_rate_matrix = [[0.0] * size for _ in agents]
        homophilic_normative_tradeoff_matrix = [[0.0] * size for _ in agents]

        for i, agent_from_id in enumerate(agents):
            agent = self.G.nodes[agent_from_id]
            connection_mask_matrix[i][i] = True
            trust_matrix[i][i] = agent["self_trust"]
            learning_rate_matrix[i][i] = agent["self_trust_learning_rate"]

            for j, agent_to_id in enumerate(agents):
                if i == j or not self._has_edge(agent_from_id, agent_to_id):
                    continue
                connection = self.G.edges[agent_from_id, agent_to_id]
                connection_mask_matrix[i][j] = True
                trust_matrix[i][j] = connection["trust"]
                learning_rate_matrix[i][j] = connection["trust_learning_rate"]
                homophilic_normative_tradeoff_matrix[i][j] = connection[
                    "homophilic_normative_tradeoff"
                ]

        return {
            "driver": deepcopy(driver),
            "agents": deepcopy(agents),
            "opinion_vector": deepcopy(opinion_vector),
            "attention_vector": deepcopy(attention_vector),
            "connection_mask_matrix": deepcopy(connection_mask_matrix),
            "trust_matrix": deepcopy(trust_matrix),
            "learning_rate_matrix": deepcopy(learning_rate_matrix),
            "homophilic_normative_tradeoff_matrix": deepcopy(homophilic_normative_tradeoff_matrix),
        }

    def __str__(self):
        lines = []

        for key, value in self.to_state().items():
            if isinstance(value, list) and value and isinstance(value[0], list):
                rows = [[str(item) for item in row] for row in value]
                widths = [max(map(len, column)) for column in zip(*rows)]

                lines.append(f" {key}:")
                for row in rows:
                    cells = "  ".join(
                        item.rjust(width) for item, width in zip(row, widths)
                    )
                    lines.append(f"  [{cells}]")
            else:
                lines.append(f" {key}: {value}")

        return "\n".join(lines)

    def from_state(self, state):
        pass


if __name__ == "__main__":
    car = Car()
    car.add_driver(
        agent_id=0,
        self_trust=0.9,
        opinion=0.5,
        attention=1,
        self_trust_learning_rate=0.1,
    )
    car.add_passenger(
        agent_id=1,
        self_trust=0.8,
        opinion=0.6,
        attention=0.5,
        self_trust_learning_rate=0.2
    )
    car.connect_agents(
        agent_from_id=0,
        agent_to_id=1,
        trust=0.7,
        trust_learning_rate=0.3,
        homophilic_normative_tradeoff=0.5
    )
    print(car)

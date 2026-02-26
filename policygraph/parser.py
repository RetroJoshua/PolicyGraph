import json
import networkx as nx

class IAMPolicyParser:
    def __init__(self):
        self.graph = nx.DiGraph()

    def parse_policy(self, policy_path):
        """Convert IAM policy JSON to graph"""
        with open(policy_path, 'r') as f:
            policy = json.load(f)

        self.graph.clear()

        for i, statement in enumerate(policy.get('Statement', [])):
            effect = statement.get('Effect', 'Allow')
            actions = statement.get('Action', [])
            resources = statement.get('Resource', [])

            # Ensure lists
            if isinstance(actions, str):
                actions = [actions]
            if isinstance(resources, str):
                resources = [resources]

            # Create nodes and edges
            for action in actions:
                for resource in resources:
                    # Add nodes
                    self.graph.add_node(
                        action,
                        type='action',
                        effect=effect
                    )
                    self.graph.add_node(
                        resource,
                        type='resource'
                    )

                    # Add edge
                    self.graph.add_edge(
                        action,
                        resource,
                        effect=effect,
                        statement_id=i
                    )

        return self.graph

    def visualize(self, output_path='policy_graph.png'):
        """Quick visualization"""
        import matplotlib.pyplot as plt

        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True,
                node_color='lightblue',
                node_size=1500,
                font_size=8,
                arrows=True)
        plt.savefig(output_path)
        print(f"✅ Graph saved to {output_path}")

# Test it
if __name__ == "__main__":
    parser = IAMPolicyParser()
    graph = parser.parse_policy("C:\\Users\\user\\Documents\\CMRIT\\projects\\PolicyGraph\\data\\raw\\samples\\s3_readwrite_bucket-objects.json")
    print(f"✅ Parsed policy: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    parser.visualize()
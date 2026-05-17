from policygraph.graph_builder import IAMGraphBuilder


def test_graph_builder_outputs_dgl_graph_with_expected_features():
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iam:PassRole", "lambda:CreateFunction"],
                "Resource": "*",
                "Condition": {"StringEquals": {"iam:PassedToService": "lambda.amazonaws.com"}},
            }
        ],
    }

    builder = IAMGraphBuilder()
    result = builder.build_graph_from_policy(policy)

    graph = result.graph
    assert graph.num_nodes() > 0
    assert graph.num_edges() > 0
    assert graph.ndata["feat"].shape[1] == 6
    assert graph.edata["feat"].shape[1] == 3

    # Ensure wildcard and sensitive features exist in at least one node
    assert float(graph.ndata["feat"][:, 4].max().item()) == 1.0
    assert float(graph.ndata["feat"][:, 5].max().item()) == 1.0

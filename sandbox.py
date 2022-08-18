import asyncio
from kademlia.network import Server
from guarantor.dht import ChangeStorage, generate_node_id



async def run():

    alpha_node_id = generate_node_id()
    node_alpha = Server(
        storage=ChangeStorage(),
        node_id=alpha_node_id
    )
    await node_alpha.listen(5678)
    await node_alpha.bootstrap(
        [
            ("0.0.0.0", 5678),
            ("0.0.0.0", 5679),
        ]
    )
    # print(f"ALPHA: {str(node_alpha.node.id)}")

    beta_node_id = generate_node_id()
    node_beta = Server(
        storage=ChangeStorage(),
        node_id=beta_node_id
    )
    await node_beta.listen(5679)
    await node_beta.bootstrap(
        [
            ("0.0.0.0", 5678),
            ("0.0.0.0", 5679),
        ]
    )
    # print(f"BETA: {str(node_beta.node.id)}")

    await node_alpha.set("my-key", "my awesome value")

    await asyncio.sleep(10)

    result = await node_beta.get("my-key")
    print(f"RESULT: {result}")


asyncio.run(run())

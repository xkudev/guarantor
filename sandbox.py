import asyncio
from kademlia.network import Server
from guarantor.dht import ChangeStorage, generate_node_id
from guarantor import schemas


WIF = "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss"


async def run():

    alpha_node_id = generate_node_id()
    node_alpha = Server(
        storage=ChangeStorage(
            node_id=alpha_node_id
        ),
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
        storage=ChangeStorage(
            node_id=beta_node_id
        ),
        node_id=beta_node_id
    )
    await node_beta.listen(5679)
    await node_beta.bootstrap(
        [
            ("0.0.0.0", 5678),
            ("0.0.0.0", 5679),
        ]
    )

    input_change = schemas.make_change(
        wif=WIF,
        doctype='foo',
        opcode='bar',
        opdata={},
    )
    input_change_data = schemas.dumps_change(input_change)

    print(f"CHANGE IN: {input_change_data}")
    # print(f"BETA: {str(node_beta.node.id)}")

    await node_alpha.set(input_change.change_id, input_change_data)

    await asyncio.sleep(10)

    output_change = await node_beta.get(input_change.change_id)
    print(f"RESULT: {output_change}")


asyncio.run(run())

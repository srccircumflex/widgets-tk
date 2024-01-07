
from src.treeselect import TreeNode, TagsConfig
from src.treeselectpopup import treepopup

if __name__ == '__main__':
    structure = (
        TreeNode("L0", "V0",
                 TreeNode("L0-0", "V0-0"),
                 TreeNode("L0-1", "V0-1"),
                 TreeNode("L0-2", "V0-2"),
                 ),
        TreeNode("L1", "V1", tags=("red",)),
        TreeNode("L2", "V2",
                 TreeNode("L2-0", "V2-0",
                          TreeNode("L2-0-0", "V2-0-0"),
                          TreeNode("L2-0-1", "V2-0-1"),
                          TreeNode("L2-0-2", "V2-0-2", checked=False),
                          ),
                 TreeNode("L2-1", "V2-1"),
                 checked=True
                 ),
    )
    addresses = (
        ("127.0.0.11", 50_000),
        ("127.0.0.12", 50_000),
        ("127.0.0.13", 50_000),
        ("127.0.0.14", 50_000),
        ("127.0.0.15", 50_000),
        ("127.0.0.16", 50_000),
    )
    instand_value = treepopup(*structure, return_mode="instand value", server_address=addresses, window_title="instand_value")
    print(f"{instand_value=}")
    receiver1 = treepopup(*structure, tags_config_update=TagsConfig(red={"background": "red"}), return_mode="receiver", server_address=addresses, window_title="receiver1")
    print(f"{receiver1.server.process.pid=}")
    receiver2 = treepopup(*structure, check_mode="single", window_mode="headless", return_mode="receiver", server_address=addresses, window_title="receiver2", server_daemon=False)
    print(f"{receiver2.server.process.pid=}")
    print("[ ! ] close/confirm the popup with title 'block_value' to continue\n")
    block_value = treepopup(*structure, check_mode="single sector", window_mode="top", window_drag=False, return_mode="wait value", server_address=addresses, window_title="block_value")
    print(f"{block_value=}")
    print("[ ! ] run: receiver1.receive(block=True)")
    print(f"{receiver1.receive(block=True)=}")
    print("[ ! ] run: receiver2.receive(block=False)")
    print(f"{receiver2.receive(block=False)=}")
    print(f"{receiver2.server.process.is_alive()=}")
    if receiver2.server.process.is_alive():
        print("[ WARN ] >")
        print(f"{receiver2.server.process.pid=}")
        print(f"is still running")
        print("< [ WARN ]")

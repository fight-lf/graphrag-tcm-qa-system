from common.neo4j_manager import neo4j_client

# 导出元数据
neo4j_client.export_tcm_metadata_to_json("tcm_metadata.json")

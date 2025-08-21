import logging

class AIOSv1PolicyRule:

    def __init__(self, rule_id, settings, parameters):

        self.rule_id = rule_id
        self.settings = settings
        self.parameters = parameters

    def eval(self, parameters, input_data, context):

        try:

            logging.info("input_data: {}".format(input_data))

            payload = input_data.get('payload', {})
            # payload structure
            # payload = {
            #     "block": block_data,
            #     "instance_id": instance_id,
            #     "cluster": cluster,
            #     "block_metrics": block_metrics,
            #     "cluster_metrics": cluster_metrics,
            #     "healthy_nodes": healthy_nodes,
            #     "extra_data": extra_data
            # }
            policy_outputs = input_data.get('policy_outputs', [])

            if input_data['action'] == 'third_party_allocate':
                logging.info(f"parameters={self.parameters}")

                if 'third_party_allocation_data' in self.parameters:
                    return self.parameters['third_party_allocation_data']

            elif input_data['action'] == 'dry_run':
                return {
                    "selection_score_data": {
                        "score": 0.9,
                        "node_info": {
                            
                        }
                    }
                }

            elif input_data['action'] == 'allocation':

                logging.info(f"parameters={self.parameters}")

                if 'allocation_data' in self.parameters:
                    return self.parameters['allocation_data']

                return {
                    "node_id": "wc-gpu-node4",
                    "gpus": [0, 1]
                }
            
            elif input_data['action'] == 'scale':

                logging.info(f"parameters={self.parameters}")

                if 'allocation_data' in self.parameters:
                    return self.parameters['allocation_data']

                return {
                    "node_id": "wc-gpu-node4",
                    "gpus": [0, 1]
                }

            elif input_data["action"] == "reassignment":

                logging.info(f"payload={payload}")
                logging.info(f"payload={payload['extra_data']}")
                if "extra_data" in payload and payload["extra_data"]:
                    logging.info(f"extra_data={payload['extra_data']}")
                    if 'allocation_data' in payload["extra_data"]:
                        self.parameters['allocation_data'] = payload["extra_data"]['allocation_data']
                        return self.parameters['allocation_data']
                    else:
                        return self.parameters['allocation_data']
                else:
                    logging.info(f"extra_data=empty so returning default allocation data")
                    return self.parameters['allocation_data']

            else:
                raise Exception(f"action {input_data['action']} not implemented")

        except Exception as e:
            raise e

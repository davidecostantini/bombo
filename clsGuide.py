def printGuide():
	guide="-----USAGE MANUAL-------"+ '\n'
	guide=guide+"run <config_name>                                                                                                           -> Launch a config"+ '\n'
	guide=guide+"backup <customer_id> <region> <instance_id> [<keep_instance_on>] [<flush_bck_snapshots>] [<keep_historical_monthlies>]      -> Backup instance volumes"+ '\n'
	guide=guide+"copy <customer_id> <region> <instance_id> <subnet> [<keep_instance_on>]                                                     -> Start instance copy"+ '\n'
	guide=guide+"scheduling <customer_id>                                                                                                    -> Apply power schedule to each instance"+ '\n'
	guide=guide+"version                                                                                                                     -> Show the app version"+ '\n'
	guide=guide+"usage                                                                                                                       -> Show this guide"+ '\n'
	guide=guide+"------------------------"+ '\n'
	print guide
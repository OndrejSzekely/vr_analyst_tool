from other import aux_functions
from arguments_parser import cmd_arguments_parser
from analyst_tool_objects import analyst_tool
aux_functions.appendParrentFolderToModules()

argumentParser = cmd_arguments_parser.prepareArgsParserWithNoConf()
analystTool = analyst_tool.AnalystTool(outputWriterType=argumentParser.parse_args().output_writer[0])
analystTool.listClassifiers()
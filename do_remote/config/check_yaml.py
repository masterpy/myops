require "yaml"
require 'erb'

def check_yml_synax(file)
   str=ERB.new(open(file).read).result 
     begin
    YAML.load(str)
        p 'OK'
   rescue Exception =>error
        p 'Synax Error: \n'+error
     end
end
if(!ARGV[0])
   STDERR.puts "arg error"
   exit 0
end
ARGV.each do |path|
   check_yml_synax(path)
end

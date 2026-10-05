using Confluent.Kafka;
using Microsoft.Extensions.Logging;
using NotificationGate.DAL;
using NotificationGate.Models;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NotificationGate.Services
{
    public class NotificationsSender
    {
        private readonly ILogger<NotificationsSender> _logger;
        private readonly kafkaClient _kafkaClient;
        private readonly ConfigStrings _configStrings;
        public NotificationsSender(ILogger<NotificationsSender> logger,
            kafkaClient kafkaClient,
            ConfigStrings configStrings)
        {
            _logger = logger;
            _kafkaClient = kafkaClient;
            _configStrings = configStrings;
        }
        public async Task Watch(string path)
        {
            var watcher = new FileSystemWatcher(path);
            watcher.InternalBufferSize = 65536;

            //watcher.NotifyFilter = NotifyFilters.Attributes;
            watcher.NotifyFilter = NotifyFilters.Attributes
                                 | NotifyFilters.CreationTime
                                 | NotifyFilters.DirectoryName
                                 | NotifyFilters.FileName
                                 | NotifyFilters.LastAccess
                                 | NotifyFilters.LastWrite
                                 | NotifyFilters.Security
                                 | NotifyFilters.Size;
            watcher.Changed += OnChanged;
            watcher.Created += OnCreated;

            watcher.Filter = "*.ready";
            watcher.IncludeSubdirectories = true;
            watcher.EnableRaisingEvents = true;

            Console.WriteLine("Press enter to exit.");
            Console.ReadLine();
        }

        private static void OnChanged(object sender, FileSystemEventArgs e)
        {
            if (e.ChangeType != WatcherChangeTypes.Changed)
            {
                return;
            }
            Console.WriteLine($"Changed: {e.FullPath}");
        }

        private async void OnCreated(object sender, FileSystemEventArgs e)
        {
            string value = $"Created: {e.FullPath}";
            string? valueFolder = Path.GetDirectoryName(e.FullPath);
            if (valueFolder == null)
            {
                Console.WriteLine("error in the folder stracure");
                return;
            }
            var files = Directory.GetFiles(valueFolder, "*.json");
            foreach (string file in files)
            {
                Console.WriteLine($"file exists: {Path.Exists(file)}, {file}");
                string content = File.ReadAllText(file);
                Console.WriteLine($"content: {content}");
                var result = await _kafkaClient.Producer.ProduceAsync(_configStrings.NotificationGetTopik,
                    new Message<Null, string> { Value = content });
                if (result == null || result.Message.Value == null)
                {
                    Console.WriteLine($"Somthing get wrong in produce");

                }
                else
                {
                    Console.WriteLine($"Send to kafka: {result.Message.Value}");
                }
                Directory.Delete(valueFolder, true);
            }
            //string notificationFile = Path.Combine(valueFolder, "alert.json");
            
            //Console.WriteLine($"{Path.Exists(notificationFile)}, {notificationFile}");
            
        }
    }
}

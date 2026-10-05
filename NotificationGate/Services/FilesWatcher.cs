using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace NotificationGate.Services
{
    public class FilesWatcher
    {
        private readonly ILogger<FilesWatcher> _logger;
        public FilesWatcher(ILogger<FilesWatcher> logger)
        {
            _logger = logger;
        }
        public void Watch(string path)
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

        private static void OnCreated(object sender, FileSystemEventArgs e)
        {
            string value = $"Created: {e.FullPath}";
            string? valueFolder = Path.GetDirectoryName(e.FullPath);
            if (valueFolder == null)
            {
                Console.WriteLine("error in the folder stracure");
                return;
            }
            string notificationFile = Path.Combine(valueFolder, "alert.json");
            
            Console.WriteLine($"{Path.Exists(notificationFile)}, {notificationFile}");
            
        }
    }
}

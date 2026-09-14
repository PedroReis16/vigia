namespace Vigia.Cloud.Config;

public class CloudOptions
{
    public const string SectionName = "Cloud";

    public string VersionsBucketName { get; set; } = string.Empty;
    public string PicturesBucketName { get; set; } = string.Empty;
    public string Endpoint { get; set; } = string.Empty;
    public string Region { get; set; } = "us-east-1";
    public string AccessKey { get; set; } = string.Empty;
    public string SecretKey { get; set; } = string.Empty;
    public bool UsePathStyle { get; set; } = true;
}

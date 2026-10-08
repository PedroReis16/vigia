using Vigia.API.Services.Clips;

namespace Vigia.API.UnitTests;

public class ClipByteRangeTests
{
    [Fact]
    public void TryResolve_SemHeader_NaoPedeFaixa()
    {
        bool resolved = ClipByteRanges.TryResolve(null, 1000, out _, out bool unsatisfiable);

        Assert.False(resolved);
        Assert.False(unsatisfiable);
    }

    [Fact]
    public void TryResolve_FaixaFechadaEAberta()
    {
        Assert.True(ClipByteRanges.TryResolve("bytes=0-99", 1000, out ClipByteRange closed, out bool closedBad));
        Assert.False(closedBad);
        Assert.Equal(new ClipByteRange(0, 99), closed);
        Assert.Equal("bytes 0-99/1000", closed.ContentRange(1000));

        Assert.True(ClipByteRanges.TryResolve("bytes=500-", 1000, out ClipByteRange open, out _));
        Assert.Equal(new ClipByteRange(500, 999), open);
    }

    [Fact]
    public void TryResolve_SufixoEFimAlemDoArquivo()
    {
        Assert.True(ClipByteRanges.TryResolve("bytes=-100", 1000, out ClipByteRange suffix, out _));
        Assert.Equal(new ClipByteRange(900, 999), suffix);

        Assert.True(ClipByteRanges.TryResolve("bytes=-5000", 1000, out ClipByteRange whole, out _));
        Assert.Equal(new ClipByteRange(0, 999), whole);

        Assert.True(ClipByteRanges.TryResolve("bytes=0-5000", 3, out ClipByteRange clamped, out _));
        Assert.Equal(new ClipByteRange(0, 2), clamped);
    }

    [Fact]
    public void TryResolve_ForaDoArquivoOuMultipart_NaoSatisfaz()
    {
        Assert.False(ClipByteRanges.TryResolve("bytes=1000-1000", 1000, out _, out bool pastEnd));
        Assert.True(pastEnd);

        Assert.False(ClipByteRanges.TryResolve("bytes=0-1,2-3", 1000, out _, out bool multipart));
        Assert.True(multipart);

        Assert.False(ClipByteRanges.TryResolve("bytes=0-1", 0, out _, out bool empty));
        Assert.True(empty);
    }

    [Fact]
    public void ObjectKeys_SeparamVideoEPoster()
    {
        Guid deviceId = Guid.Parse("11111111-1111-1111-1111-111111111111");
        Guid clipId = Guid.Parse("22222222-2222-2222-2222-222222222222");

        Assert.Equal("clips/11111111-1111-1111-1111-111111111111/22222222-2222-2222-2222-222222222222.mp4", ClipObjectKeys.For(deviceId, clipId));
        Assert.Equal("clips/11111111-1111-1111-1111-111111111111/22222222-2222-2222-2222-222222222222.jpg", ClipObjectKeys.Poster(deviceId, clipId));
    }
}

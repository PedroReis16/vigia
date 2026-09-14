using Vigia.Models.Enums;

namespace Vigia.Models.UnitTests;

public class ErrorCodesTests
{
    [Fact]
    public void FiwareErrorCodes_HaveStableValues()
    {
        Assert.Equal(35, (int)ErrorCodes.FIWARE_COMMAND_FAILED);
        Assert.Equal(36, (int)ErrorCodes.FIWARE_PROVISION_FAILED);
    }
}

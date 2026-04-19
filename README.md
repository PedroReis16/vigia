# VIGIA - Sistema doméstico para o monitoramento de quedas



## Dispositivo embarcado

O ambiente embarcado esta sendo utilizado uma placa Raspberry PI 5 com 8 GB de memória RAM de processamento, sendo executado com o Raspberry PI OS Lite 64-bits como sistema operacional principal.

### Pré-Requisitos

Antes de iniciar a configuração, certifique-se:
    - A placa foi configurada pelo Raspberry Pi Imager com usuário e senha definidos
    - Acesso físico à placa (monitor + teclado) ou acesso remoto via SSH com senha ainda ativo
    - Conta criada em `login.tailscale.com`

### Configurando o ambiente

- `Hostname e mDNS`
    O mDNS permite acessar o dispositivo pelo nome em qualquer rede local, sem precisar conhecer o IP da placa

    ```
        # Alterar o hostname
        sudo hostnamectl set-hostname vigia

        # Garantir que avahi sobre no boot

        sudo systemctl enable avahi-daemon
        sudo systemctl start avahi-daemon

    ```

    Após configurado, o dispotivio poderá ser acessado em qualquer rede local pelo endereço `vigia.local`.
    ```
        ssh vigia@vigia.local
    ``` 


- `SSH`  
    O SSH esta configurado para ser a única forma de acesso ao sistema, garantindo que apenas dispositivos confiáveis tenham acesso ao terminal da placa.

    - **Habilitar o SSH**
    
        ```
            sudo systemctl enable ssh #Habilita o serviço SSH para iniciar automaticamente
            sudo systemctl start ssh #Inicia o SSH
        ```

    - **Adicionar a chave pública no Pi**

        ```
            mkdir -p ~/.ssh && chmod 700 ~/.ssh
            echo "<CHAVE_PUBLICA>" >> ~/.ssh/authorized_keys   #Substitua `<CHAVE_PUBLICA>` pela sua chave
            chmod 600 ~/.ssh/authorized_keys

            sudo systemctl restart ssh
        ```

        - Nesse ponto, a chave pública foi configurada e o acesso deve estar habilitado
            
            ```
                exit #Desconectar do ambiente
                
                ssh vigia@<IP_PLACA> #Acesse novamente, se não pedir senha, o acesso foi realizado com sucesso via SSH
            ```

    - `Desabilitar autenticação por senha no Pi` **(Execute essa etapa apenas quando tiver certeza que a conexão por SSH esta funcionando)**

        Nessa etapa, etapa iremos configurar a placa de maneira que o acesso fique habilitado apenas chaves SSH

        - **Edite o arquivo de configuração do cloud-init**
            O arquivo de cloud-init é utilizado no ambiente para configuração do sistema operacional para ambiente em nuvem, tendo prioridade de execução sobre os demais arquivos de configuração

            - **Acesse o arquivo**
                ```
                    sudo nano /etc/ssh/sshd_config.d/50-cloud-init.conf
                ```

            - **Altere o conteúdo para**

                ````
                    PasswordAuthentication no

                ```
        - **Edite o arquivo sshd_config**

            ```
                sudo nano /etc/ssh/sshd_config #Habilita o modo de edição no arquivo de configurações
            ```

            - **Ajuste as seguintes linhas**

                ```
                    PasswordAuthentication no        # Desabilita a opção de login por senha
                    PubkeyAuthentication yes         # Habilita a autenticação por chave SSH
                    PermitRootLogin no               # Usuário root não pode realizar o login remoto
                    ListenAddress 0.0.0.0            # Habilita o acesso de qualquer IP
                    ListenAddress :: 
                    ClientAliveInterval 60           # Tempo em segundos entre verificações de conexão
                    ClientAliveCountMax 3            # Número de verificações antes de encerrar a sesssão
                ```

        - **Reiniciar o serviço**

            Reinicie o serviço SSH e verifique se as configurações foram aplicadas

            ```
                sudo systemctl restart ssh

                # Confirmar que senha está bloqueada
                sudo sshd -T | grep passwordauthentication

                # Deve retornar: passwordauthentication no
            ```

- `Acesso remoto`

    Para permitir que o dispositivo embarcado possa ser acessado de qualquer ambiente, sem a necessidade do terminal e o embarcado estarem conectados a mesma rede, utilizamos o `Tailscale`. O Tailscale cria uma rede VPN entre todos os dispositivos da mesma conta, permitindo acesso remoto de qualquer lugar sem abrir portas no roteador.


    - **Instalação** 
        ```
            curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up
        ```

        Após a execução desse comando, será retornado uma URL para autenticação do usuário dentro do Tailscale, cole-a no navegador do computador e realize a autenticação. Após finalizar, o dispositivo já estará configurado.

    - **Verificar dispositivos e IPs**

        ```
            # Listar dispositivos da rede Tailscale
            tailscale status

            #Ver o IP do dispositivo atual
            tailscale ip
        ```

    - **Conectar ao Pi remotamente**
        ```
            # Por IP Tailscale

            ssh vigia@100.X.X.X

            $ Por magicDNS (URL fixa para acesso)
            ssh vigia@<MAGIC_DNS>
        ```

    Com o Tailscale, os dispositivos (Board | Host) pode ser acessados remotamente de qualquer lugar, desde que estejam conectados a internet e vinculados a mesma conta do tailscale.

- `Gerenciamento de redes Wi-Fi`

    O NetworkManager gerencia as conexões de rede. Cada rede salva recebe uma prioridade - quanto maior o número, maior a preferência. O Pi conecta automaticamente à rede disponível de maior prioridade.

    - **Inteface terminal (nmtui)**

        Para adicionar ou gerenciar redes com uma interface no terminal
        ```
            sudo nmtui
        ```
            
        - Active a connection -> Selecionar rede -> digitar senha
        - Edit a connection -> Gerenciar redes salvar

    - **Comandos rápidos (CLI)**

        ````
            # Listar redes disponíveis

            nmcli device wifi list

            # Conectar a uma rede salva
            sudo nmcli device wifi connect "<NOME REDE>"

            # Conectar e salvar uma nova rede
            sudo nmcli device wifi connect "<NOME REDE>" password "<SENHA DA REDE>"

            # Definir prioridade da rede
            sudo nmcli connection modify "<NOME REDE>" connection.autoconnect-priority 10

            # Ver todas as redes salvas com prioridade
            nmcli -f NAME, TYPE, AUTOCONNECT, AUTOCONNECT-PRIORITY connection show

            # Remover uma rede salva
            sudo nmcli connection delete "<NOME REDE>"
        ```

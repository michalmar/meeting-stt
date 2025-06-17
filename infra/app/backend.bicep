param name string
param location string = resourceGroup().location
param tags object = {}

param identityName string
param containerRegistryName string
param containerAppsEnvironmentName string
param applicationInsightsName string
param exists bool

param azureOpenaiResourceName string = 'dreamv2' 
param azureOpenaiDeploymentName string = 'gpt-4o'
param azureOpenaiDeploymentNameMini string = 'gpt-4o-mini'
param azureOpenaiDeploymentNameEmbedding string = 'text-embedding-3-large'
@description('Name of the additional OpenAI resource for transcription')
param azureOpenaiTranscribeResourceName string = 'transcribeopenai'
@description('Deployment name for the transcription model')
param azureOpenaiTranscribeDeploymentName string = 'gpt-4o-audio-preview'

@description('Custom subdomain name for the OpenAI resource (must be unique in the region)')
param customSubDomainName string

@description('Name of the storage account')
param storageName string

@secure()
param appDefinition object

@description('Principal ID of the user executing the deployment')
param userPrincipalId string

// Add parameter to receive the ACA subnet ID from main.bicep
param acaSubnetId string
param defaultSubnetId string

@description('The ID of the target virtual network for private DNS association')
param vnetId string

@description('Name of the Speech resource')
param speechServiceName string

var appSettingsArray = filter(array(appDefinition.settings), i => i.name != '')
var secrets = map(filter(appSettingsArray, i => i.?secret != null), i => {
  name: i.name
  value: i.value
  secretRef: i.?secretRef ?? take(replace(replace(toLower(i.name), '_', '-'), '.', '-'), 32)
})
var env = map(filter(appSettingsArray, i => i.?secret == null), i => {
  name: i.name
  value: i.value
})

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: applicationInsightsName
}

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(subscription().id, resourceGroup().id, identity.id, 'acrPullRole')
  properties: {
    roleDefinitionId:  subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalType: 'ServicePrincipal'
    principalId: identity.properties.principalId
  }
}

module fetchLatestImage '../modules/fetch-container-image.bicep' = {
  name: '${name}-fetch-image'
  params: {
    exists: exists
    name: name
  }
}

// Create Storage Account with private endpoint in the default subnet

resource storageAcct 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }
}

// Create a blob container named "data" in the storage account
resource dataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  name: '${storageAcct.name}/default/data'
  dependsOn: [storageAcct]
  properties: {
    publicAccess: 'None'
  }
}

resource peStorage 'Microsoft.Network/privateEndpoints@2021-05-01' = {
  name: 'pe-storage-${uniqueString(name, location)}'
  location: location
  properties: {
    subnet: {
      id: defaultSubnetId // Use the defaultSubnetId parameter instead of network module output
    }
    privateLinkServiceConnections: [
      {
        name: 'storageLink'
        properties: {
          privateLinkServiceId: storageAcct.id
          groupIds: [
            'blob'
          ]
        }
      }
    ]
  }
}

resource peSpeech 'Microsoft.Network/privateEndpoints@2021-05-01' = {
  name: 'pe-speech-${uniqueString(speechServiceName, location)}'
  location: location
  properties: {
    subnet: {
      id: defaultSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'speechLink'
        properties: {
          privateLinkServiceId: speech.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource peOpenai 'Microsoft.Network/privateEndpoints@2021-05-01' = {
  name: 'pe-openai-${uniqueString(azureOpenaiResourceName, location)}'
  location: location
  properties: {
    subnet: {
      id: defaultSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'openaiLink'
        properties: {
          privateLinkServiceId: openai.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}
// Private endpoint for the additional OpenAI (transcribe) resource in swedencentral
resource peOpenaiTranscribe 'Microsoft.Network/privateEndpoints@2021-05-01' = {
  name: 'pe-openai-transcribe-${uniqueString(azureOpenaiTranscribeResourceName, 'swedencentral')}'
  location: location
  properties: {
    subnet: {
      id: defaultSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'openaiLink'
        properties: {
          privateLinkServiceId: openaiTranscribe.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource app 'Microsoft.App/containerApps@2023-05-02-preview' = {
  name: name
  location: location
  tags: union(tags, {'azd-service-name':  'backend' })
  dependsOn: [ acrPullRole ]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress:  {
        external: true
        targetPort: 3100
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          identity: identity.id
        }
      ]
      secrets: union([
      ],
      map(secrets, secret => {
        name: secret.secretRef
        value: secret.value
      }))
    }
    template: {
      containers: [
        {
          image: fetchLatestImage.outputs.?containers[?0].?image ?? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          name: 'main'
          env: union([
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsights.properties.ConnectionString
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openai.properties.endpoint
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: identity.properties.clientId
            }
            {
              name: 'PORT'
              value: '80'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_ENDPOINT'
              value: storageAcct.properties.primaryEndpoints.blob
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_ID'
              value: storageAcct.id
            }
            {
              name: 'UAMI_RESOURCE_ID'
              value: identity.id
            }
            {
              name: 'AZURE_SPEECH_ENDPOINT'
              value: 'https://${speech.properties.customSubDomainName}.cognitiveservices.azure.com/'
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: speech.location
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: azureOpenaiDeploymentName
            }
            {
              name: 'AZURE_SPEECH_KEY'
              value: speech.listKeys().key1
            }
            {
              name: 'MODEL_NAME'
              value: azureOpenaiDeploymentName
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT_TRANSCRIBE'
              value: openaiTranscribe.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE'
              value: azureOpenaiTranscribeDeploymentName
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storageAcct.name
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_KEY'
              value: storageAcct.listKeys().keys[0].value
            }
            
          ],
          env,
          map(secrets, secret => {
            name: secret.name
            secretRef: secret.secretRef
          }))
          resources: {
            cpu: json('2.0')
            memory: '4.0Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

resource openai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: azureOpenaiResourceName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: customSubDomainName
  }
}

// Define the OpenAI deployment
resource openaideployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: azureOpenaiDeploymentName
  parent: openai
  sku: {
    name: 'DataZoneStandard'
    capacity: 100
  }
  properties: {
    model: {
      // name: 'gpt-4o'
      // format: 'OpenAI'
      // version: '2024-11-20'
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
      
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'

  }
}


resource userOpenaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai.id, userPrincipalId, 'Cognitive Services OpenAI User')
  scope: openai
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
} 

resource appOpenaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai.id, identity.id, 'Cognitive Services OpenAI User')
  scope: openai
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}

resource openaiTranscribe 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: azureOpenaiTranscribeResourceName
  location: 'swedencentral'
  sku: {
    name: 'S0'
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: azureOpenaiTranscribeResourceName
  }
}

resource openaiTranscribeDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  name: azureOpenaiTranscribeDeploymentName
  parent: openaiTranscribe
  sku: {
    name: 'GlobalStandard'
    capacity: 250
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-audio-preview'
      version: '2024-12-17'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

resource openaiTranscriberWhisper 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: openaiTranscribe
  name: 'whisper'
  sku: {
    name: 'Standard'
    capacity: 3
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'whisper'
      version: '001'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [
    openaiTranscribeDeployment
  ]
}


// Grant Cognitive Services User role to user for the transcribe OpenAI resource
resource userOpenaiTranscribeRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openaiTranscribe.id, userPrincipalId, 'Cognitive Services OpenAI User')
  scope: openaiTranscribe
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}

// Grant Cognitive Services User role to app managed identity for the transcribe OpenAI resource
resource appOpenaiTranscribeRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openaiTranscribe.id, identity.id, 'Cognitive Services OpenAI User')
  scope: openaiTranscribe
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}

resource speech 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechServiceName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'SpeechServices'
  properties: {
    customSubDomainName: speechServiceName
    // Add any required properties here
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Grant Cognitive Services User role to user
resource userSpeechRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speech.id, userPrincipalId, 'Cognitive Services Speech User')
  scope: speech
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
  }
}

// Grant Cognitive Services User role to app managed identity
resource appSpeechRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(speech.id, identity.id, 'Cognitive Services Speech User')
  scope: speech
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f2dc8367-1007-4938-bd23-fe263f013447')
  }
}

resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAcct.id, identity.id, 'Storage Blob Data Contributor')
  scope: storageAcct
  properties: {
    principalId: speech.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

resource storageRoleAssignmentApp 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAcct.id, identity.id, 'Storage Blob Data Contributor2')
  scope: storageAcct
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

resource userStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAcct.id, userPrincipalId, 'Storage Blob Data Contributor')
  scope: storageAcct
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}


output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output name string = app.name
output uri string = 'https://${app.properties.configuration.ingress.fqdn}'
output id string = app.id
output azure_endpoint string = openai.properties.endpoint
output storageAccountId string = storageAcct.id
output storageAccountEndpoint string = storageAcct.properties.primaryEndpoints.blob
output userAssignedIdentityId string = identity.id
output speechServiceEndpoint string = 'https://${speech.properties.customSubDomainName}.cognitiveservices.azure.com/'
output speechServiceRegion string = speech.location
#disable-next-line outputs-should-not-contain-secrets
output speechServiceKey string = speech.listKeys().key1
output azureOpenaiDeploymentName string = openaideployment.name

output azureOpenaiTranscribeDeploymentName string = openaiTranscribeDeployment.name
output azureOpenaiTranscribeEndpoint string = openaiTranscribe.properties.endpoint

output storageAccountName string = storageAcct.name
#disable-next-line outputs-should-not-contain-secrets
output storageAccountKey string = storageAcct.listKeys().keys[0].value

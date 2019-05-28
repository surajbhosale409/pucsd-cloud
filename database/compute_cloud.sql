/*
############### R-Database Schema (As per discussion on - 14th Oct 2018) ##################

AvailableExecutionFrameworks -
    frameworkID(pk),
    toolType(fk),
    makefile,
    maxRAMAllowed,
    maxDiskSpaceAllowed,
    maxExecutionTimeAllowed,
    maxRequestSize,
    frameworkDefaultParams,
    status(fk? Like active/inactive etc)

ToolTypes -
    toolType(pk)

HandlerTypes -
    handlerType(pk),
    handlerImagePath,

toolsHandlersAssociation-
    toolType(fk),
    handlerType(fk),
    [Combinely pk]

frameworkServiceAssociations - 
    serviceID (fk),  
    frameworkID (fk),
    [Combinely pk]

services -
    serviceID(pk),
    description,
    serviceDefaultParams,
    status(fk? Like active/inactive etc),

clients -
    clientID(pk),

clientJobs -
    jobID(pk),
    clientID(fk),
    serviceID + frameworkID (composite fk)
    jobParams,
    jobSourceCodePath,
    jobStatus, (validating, accepted, rejected,queued, in progress, completed)
    jobStatusDetails,(v-result,in-prog-estimationoftime, completed-success-fail,queued-seq-no)
    jobOutputFilePath,

handlerInstances - 
    handlerInstanceID(pk),
    launchedTimestamp,
    status,
    loadStatus,
    garbageStatus,
    ipv4,
    hostID(fk)

jobHandlerInstancesAssociations -
    jobID(fk),
    handlerInstanceID(fk),
    handlerType(fk)
    jobStartTimestamp,
    jobFinishedStatus,

#######################################################################################################
*/

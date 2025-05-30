// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type BackfillTableFragment = {
  __typename: 'PartitionBackfill';
  id: string;
  status: Types.BulkActionStatus;
  isAssetBackfill: boolean;
  isValidSerialization: boolean;
  numPartitions: number | null;
  timestamp: number;
  partitionSetName: string | null;
  hasCancelPermission: boolean;
  hasResumePermission: boolean;
  partitionNames: Array<string> | null;
  partitionSet: {
    __typename: 'PartitionSet';
    id: string;
    mode: string;
    name: string;
    pipelineName: string;
    repositoryOrigin: {
      __typename: 'RepositoryOrigin';
      id: string;
      repositoryName: string;
      repositoryLocationName: string;
    };
  } | null;
  assetSelection: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  tags: Array<{__typename: 'PipelineTag'; key: string; value: string}>;
  error: {
    __typename: 'PythonError';
    message: string;
    stack: Array<string>;
    errorChain: Array<{
      __typename: 'ErrorChainLink';
      isExplicitLink: boolean;
      error: {__typename: 'PythonError'; message: string; stack: Array<string>};
    }>;
  } | null;
};

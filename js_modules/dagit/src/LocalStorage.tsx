import * as React from "react";

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  current: string;
}

export interface IExecutionSessionPlan {
  steps: Array<{
    name: string;
    kind: string;
    solid: {
      name: string;
    };
  }>;
}

export interface IExecutionSession {
  key: string;
  name: string;
  environmentConfigYaml: string;
  mode: string | null;
  solidSubset: string[] | null;

  // this is set when you execute the session and freeze it
  runId?: string;
  configChangedSinceRun: boolean;
}

export type IExecutionSessionChanges = Partial<IExecutionSession>;

const DEFAULT_SESSION: IExecutionSession = {
  key: "default",
  name: "Workspace",
  environmentConfigYaml: "",
  mode: null,
  solidSubset: null,
  runId: undefined,
  configChangedSinceRun: false
};

export function applySelectSession(data: IStorageData, key: string) {
  return { ...data, current: key };
}

export function applyRemoveSession(data: IStorageData, key: string) {
  const next = { current: data.current, sessions: { ...data.sessions } };
  const idx = Object.keys(next.sessions).indexOf(key);
  delete next.sessions[key];
  if (next.current === key) {
    const remainingKeys = Object.keys(next.sessions);
    next.current = remainingKeys[idx] || remainingKeys[0];
  }
  return next;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges
) {
  const saved = data.sessions[key];
  if (
    changes.environmentConfigYaml &&
    changes.environmentConfigYaml !== saved.environmentConfigYaml &&
    saved.runId
  ) {
    changes.configChangedSinceRun = true;
  }

  return {
    current: data.current,
    sessions: { ...data.sessions, [key]: { ...saved, ...changes } }
  };
}

export function applyCreateSession(
  data: IStorageData,
  initial: IExecutionSessionChanges = {}
) {
  const key = `s${Date.now()}`;

  return {
    current: key,
    sessions: {
      ...data.sessions,
      [key]: Object.assign({}, DEFAULT_SESSION, initial, {
        configChangedSinceRun: false,
        key
      })
    }
  };
}

// StorageProvider component that vends `IStorageData` via a render prop

export type StorageHook = [
  IStorageData,
  React.Dispatch<React.SetStateAction<IStorageData>>
];

let _data: IStorageData | null = null;
let _dataNamespace = "";

function getStorageDataForNamespace(namespace: string) {
  if (_data && _dataNamespace === namespace) {
    return _data;
  }

  let data: IStorageData = {
    sessions: {},
    current: ""
  };
  try {
    const jsonString = window.localStorage.getItem(`dagit.${namespace}`);
    if (jsonString) {
      data = Object.assign(data, JSON.parse(jsonString));
    }
  } catch (err) {
    // noop
  }
  if (Object.keys(data.sessions).length === 0) {
    data = applyCreateSession(data);
  }
  if (!data.sessions[data.current]) {
    data.current = Object.keys(data.sessions)[0];
  }

  _data = data;
  _dataNamespace = namespace;

  return data;
}

function writeStorageDataForNamespace(namespace: string, data: IStorageData) {
  _data = data;
  _dataNamespace = namespace;
  window.localStorage.setItem(`dagit.${namespace}`, JSON.stringify(data));
}

/* React hook that provides local storage to the caller. A previous version of this
loaded data into React state, but changing namespaces caused the data to be out-of-sync
for one render (until a useEffect could update the data in state). Now we keep the
current localStorage namespace in memory (in _data above) and React keeps a simple
version flag it can use to trigger a re-render after changes are saved, so changing
namespaces changes the returned data immediately.
*/
export function useStorage({ namespace }: { namespace: string }): StorageHook {
  const [version, setVersion] = React.useState<number>(0);

  const onSave = (newData: IStorageData) => {
    writeStorageDataForNamespace(namespace, newData);
    setVersion(version + 1); // trigger a React render
  };

  return [getStorageDataForNamespace(namespace), onSave];
}

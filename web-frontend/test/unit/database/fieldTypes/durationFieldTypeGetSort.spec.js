/* eslint-disable */
import { TestApp } from '@baserow/test/helpers/testApp'
import { firstBy } from 'thenby'
import workspaceStore from '@baserow/modules/core/store/workspace'

const tableRows = [
  {
    id: 1,
    order: '1.00000000000000000000',
    field: 120,
  },
  {
    id: 2,
    order: '2.00000000000000000000',
    field: '0:1:0',
  },
  {
    id: 3,
    order: '3.00000000000000000000',
    field: null,
  },
  {
    id: 4,
    order: '4.00000000000000000000',
    field: 86400,
  },
  {
    id: 5,
    order: '4.00000000000000000000',
    field: 3600,
  },
  {
    id: 6,
    order: '5.00000000000000000000',
    field: '2:0:0.123',
  },
  {
    id: 7,
    order: '6.00000000000000000000',
    field: '1.12'
  }
]

describe('LastModifiedByFieldType.getSort()', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('sorting based on the provided duration value', () => {
    const durationField = {}
    const durationType = testApp._app.$registry.get('field', 'duration')

    expect(durationType.getCanSortInView(durationField)).toBe(true)

    const ASC = durationType.getSort('field', 'ASC', durationField)
    const sortASC = firstBy().thenBy(ASC)
    const DESC = durationType.getSort('field', 'DESC', durationField)
    const sortDESC = firstBy().thenBy(DESC)

    tableRows.sort(sortASC)

    const sorted = tableRows.map((obj) =>
      obj.field
    )
    const expected = [
      null,
      '1.12',
      '0:1:0',
      120,
      3600,
      '2:0:0.123',
      86400,
    ]

    expect(sorted).toEqual(expected)

    tableRows.sort(sortDESC)

    const sortedReversed = tableRows.map((obj) =>
      obj.field
    )

    const expectedReversed = [
      86400,
      '2:0:0.123',
      3600,
      120,
      '0:1:0',
      '1.12',
      null,
    ]

    expect(sortedReversed).toEqual(expectedReversed)
  })
})
